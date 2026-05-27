#include "EventSimulator.hh"

EventSimulator::EventSimulator() { rand.SetSeed(0); }

void EventSimulator::SetConfig(string fname) {
    ifstream config_file(fname);
    config_file >> config;

    auto contain = [=](string str) {
        return (config.find(str) != config.end());
    };

    // basic info
    group = config.at("group");
    run = config.at("run");
    file = config.at("file");
    total_events = config.at("total_events");
    {
        PandaXDataSource pds;
        pmt_map = pds.loadPmtMap(run);
        for (auto pm: pmt_map) {
            pmt_index_map[pm.second.pmtNo] = pm.second.pmtId;
        }
    }

    // simulator
    drop_hit_simulator.run_number = run;
    sim_pe_builder.SetRun(run);

    // info printing
    if (contain("verbose")) {
        verbose = config["verbose"];
    }

    if (contain("event_build_method")) {
        event_build_method = config["event_build_method"].get<string>();
        if (std::find(eb_methods.begin(), eb_methods.end(),
                      event_build_method) == eb_methods.end()) {
            cout << "unknown event build method. use fix window" << endl;
            event_build_method = "1ms_fix_window";
        }
        cout << "event build method: " << event_build_method << endl;
    }

    // s1 method
    auto s1_method = config["s1_method"];

    if (s1_method["method"] == "drop_hit") {
        drop_hit_s1 = true;
        string s1_pool_dir = s1_method["s1_pool"].get<string>();
        drop_hit_simulator.LoadSignal(s1_pool_dir);
        if (s1_method.find("photon_range") != s1_method.end()) {
            photon_range = s1_method["photon_range"].get<std::pair<int, int>>();
        }
    } else if (s1_method["method"] == "wf_simu") {
        wf_simu_s1 = true;
        s1_simulator = S1Simulator(run);
        photon_range = s1_method["photon_range"].get<std::pair<int, int>>();
        // set photon range
        // set s1 timing dir
    } else if (s1_method["method"] == "quick") {
        quick_s1 = true;
    } else if (s1_method["method"] == "no_s1") {
        no_s1 = true;
    }

    // s2 method
    auto s2_method = config["s2_method"];

    if (s2_method["method"] == "se_assemble") {
        se_assemble_s2 = true;

        { // basic info
            vector<int> e_range = s2_method["electron_range"];
            min_e = e_range[0];
            max_e = e_range[1];
            if (s2_method.find("diffusion_coeff") != s2_method.end())
                diffusion_coeff = s2_method["diffusion_coeff"].get<float>();
            if (s2_method.find("eee_scaling") != s2_method.end())
                eee_scaling = s2_method["eee_scaling"].get<float>();
        }

        s2_pool.LoadSortedSEPool(s2_method["se_pool"].get<string>(),
                                 s2_method["max_pool_size"].get<int>());

        if (s2_method.find("drift_time") != s2_method.end()) {
            drift_time = s2_method["drift_time"];
        }
        if (s2_method.find("ms_histogram") != s2_method.end()) {
            enable_ms = true;
            string ms_histogram = s2_method["ms_histogram"];
            TFile *f = TFile::Open(ms_histogram.c_str());
            hist_qt = (TH2F *)f->Get("q_dt")->Clone();
            hist_qt->SetDirectory(0);
            cout << "Multi scattering histogram: " << ms_histogram << endl;
            delete f;
        }

        // pos generating
        auto pos_method = s2_method["position_generating"];
        if (pos_method["method"] == "most_close") {
            most_close_position = true;
            vector<float> pos = pos_method["position"];
            if (pos.size() != 0) {
                most_close_x = pos[0];
                most_close_y = pos[1];
                printf("use fix pos: [%.1f, %.1f]\n", most_close_x,
                       most_close_y);
            }
            if (pos_method.find("use_paf_pattern") != pos_method.end() &&
                pos_method["use_paf_pattern"].get<bool>() == true) {
                use_paf_pattern = pos_method.at("use_paf_pattern");
                string pafname = pos_method.at("paf_name").get<string>();
                paf = new PosRecPAF();
                {
                    PandaXDataSource pds;
                    paf->init(pds, run, pafname);
                }
            }
        } else if (pos_method["method"] == "fix") {
            fix_position = true;
            vector<float> pos = pos_method["position"];
            fix_x = pos[0];
            fix_y = pos[1];
        } else if (pos_method["method"] == "random") {
            random_position = true;
        }

    } else if (s2_method["method"] == "wf_simu") {
        wf_simu_s2 = true;
    } else if (s2_method["method"] == "no_s2") {
        no_s2 = true;
    }

    if (contain("delay_signal_method")) {
        auto method = config["delay_signal_method"];
        use_afterpulse = method["afterpulse"];
        use_delayion = method["delay_ionization"];
        if (use_afterpulse) {
            ap_simulator.LoadAfterPulseFile();
        }
        if (use_delayion) {
            delay_ion_pool.LoadSignal(
                method["delay_ionization_SE_pool"].get<string>(),
                method["max_pool_size"].get<int>());
            if (method.find("delay_ionization_prob_scaling") != method.end()) {
                di_simulator.ScaleProbability(
                    method["delay_ionization_prob_scaling"].get<float>());
            }
        }
    }

    if (contain("noise_method")) {
        auto noise_method = config["noise_method"];
        if (noise_method["method"] == "simulation") {
            cout << "use random spe" << endl;
            use_random_spe = true;
            spe_rate = noise_method["spe_rate"].get<float>();
        } else if (noise_method["method"] == "data_driven") {
            cout << "use data driven noise" << endl;
            use_data_driven_noise = true;
            noise_pool.LoadPool(noise_method["pool"].get<string>(),
                                noise_method["max_pool_size"].get<int>());
        } else if (noise_method["method"] == "no") {
            // do nothing
        }
    }

    if (contain("nest")) {
        auto nest_method = config["nest"];
        enable_nest = true;
        auto file_name = nest_method["file"].get<string>();
        auto tree_name = nest_method["tree"].get<string>();
        nest_reader.SetTree(file_name, tree_name);
        nest_info = nest_reader.GetPhotonElectronArray(total_events);
    }

    if (contain("geant4")) {
        auto g4_method = config["geant4"];
        enable_geant4 = true;
        drift_g4 = g4_method["drift_time"];
        auto deposition_dir = g4_method["file"].get<string>();
        cout << "deposition dir: " << deposition_dir << endl;
        ifstream f(deposition_dir);
        while (!f.eof()) {
            float v;
            f >> v;
            deposition_array.push_back(v);
        }
    }
}

PhysicalEventData EventSimulator::BuildEvent() {
    auto hd = Generate(event_build_method);
    PhysicalEventData pe;
    if (event_build_method == eb_methods[0]) {
        pe = sim_pe_builder.GetDirectEvent(hd);
    } else if (event_build_method == eb_methods[1]) {
        pe = sim_pe_builder.GetDirectEvent(hd, 1100 * 250); // < 1.1 ms
    } else if (event_build_method == eb_methods[2]) {
        pe = sim_pe_builder.GetInOrderEventByTime(hd, 5 * 250 *
                                                          1000); // prev s2 5 ms
    }
    return pe;
}

HitData EventSimulator::Generate(string event_build_method) {

    // jump to Geant4 generate
    if (enable_geant4)
        return G4Generate();

    // define hit data
    HitData hd;
    hd.runNumber = run;
    hd.groupNumber = group;

    ///////////////////////////////
    // start waveform simulation //
    ///////////////////////////////

    // define Npe, Ne, dt
    int photon = 1;
    int electron = 1;
    float drift_time = rand.Uniform(0, 840);

    // NEST Npe, Ne, dt
    if (enable_nest) {
        photon = nest_info.front().Npe;
        electron = nest_info.front().Ne;
        drift_time = nest_info.front().drift_time;
        nest_info.erase(nest_info.begin());
    } else {
        float pmin = photon_range.first;
        float pmax = photon_range.second;
        if (pmin == 0 || pmax == 0 || pmin > pmax) {
            pmin = 0;
            pmax = 10;
        }
        photon = rand.Uniform(pmin, pmax);
        float sim_frac = float(sim_events) / float(total_events);
        electron = int(float(max_e - min_e + 1) * sim_frac) + min_e;
    }

    // MS Ne and dt
    if (enable_ms) {
        double ms_charge, ms_dt;
        hist_qt->GetRandom2(ms_charge, ms_dt);
        electron = ms_charge / 19.2; // SEG
        drift_time = ms_dt;
    }

    // randomnize S2 x y
    float theta = rand.Uniform(0, 2 * 3.1415926535);
    float r = sqrt(rand.Uniform(0, 360) * 1e3);
    float x = r * cos(theta);
    float y = r * sin(theta);

    // truth info
    truth.photon.push_back(photon);
    truth.electron.push_back(electron);
    truth.drift_time.push_back(drift_time);
    truth.x.push_back(x);
    truth.y.push_back(y);
    truth.r2.push_back(r * r);

    // anchoring time
    float total_wf_length = 3;            // 3 ms
    uint64_t prev_s1_window = 250 * 1000; // 1 ms
    uint64_t post_s1_window = 250 * 2000; // 2 ms
    if (event_build_method == eb_methods[0]) {
        // prev s1 1 ms + post s1 2 ms
        total_wf_length = 3;
        prev_s1_window = 250 * 1000;
    } else if (event_build_method == eb_methods[1]) {
        // prev s2 1 ms + post s2 0.1 ms
        total_wf_length = 1.1;
        prev_s1_window = uint64_t(1000 / 4e-3 - drift_time / 4e-3);
    } else if (event_build_method == eb_methods[2]) {
        // prev s2 5 ms + post s2 5 ms
        total_wf_length = 10;
        prev_s1_window = 5 * 250 * 1000 - uint64_t(drift_time / 4e-3);
    }
    post_s1_window = uint64_t(total_wf_length / 4e-6) - prev_s1_window;

    // s2 modification
    electron = rand.Binomial(electron, eee_scaling);

    ///////////////////////
    // signal simulation //
    ///////////////////////

    // S1
    HitData hds1;
    if (drop_hit_s1) {
        hds1 = drop_hit_simulator.GetDroppedSignal(photon, drift_time,
                                                   prev_s1_window);
    } else if (wf_simu_s1) {
        hds1 = s1_simulator.GetS1(photon, prev_s1_window);
    } else if (quick_s1) {
        hds1 = GetQuickS1(prev_s1_window);
    } else if (no_s1) {
        // do nothing
    }
    if (photon > 0 && !no_s1) { // truth info
        truth.qS1True.push_back(GetChargeByHits(hds1.hitsVec));
        truth.tS1True.push_back(hds1.hitsVec.front().startTime);
        append_hd(hd, hds1);
    } else {
        truth.qS1True.push_back(0);
        truth.tS1True.push_back(0);
    }

    // S1 delay signals
    if ((use_afterpulse || use_delayion) && !no_s1) {
        HitData hds1more = GetDelaySignals(hds1);
        append_hd(hd, hds1more);
    }

    // S2
    HitData hds2;
    if (se_assemble_s2) {
        if (most_close_position) {
            hds2 = MostCloseGenerate(electron, drift_time, prev_s1_window, x, y, use_paf_pattern);
        } else if (fix_position) {
            hds2 = FixGenerate();
        } else {
            hds2 = RandomGenerate();
        }
    } else if (wf_simu_s2) { // do nothing
    } else if (no_s2) {      // do nothing
    }
    if (electron > 0 && se_assemble_s2) { // truth info
        truth.qS2True.push_back(GetChargeByHits(hds2.hitsVec));
        truth.tS2True.push_back(hds2.hitsVec.front().startTime);
        append_hd(hd, hds2);
    } else {
        truth.qS2True.push_back(0);
        truth.tS2True.push_back(0);
    }

    // S2 delay signals
    if (electron > 0 && se_assemble_s2 && (use_afterpulse || use_delayion)) {
        HitData hds2more = GetDelaySignals(hds2);
        append_hd(hd, hds2more);
    }

    // noise
    if (use_random_spe) {
        auto spe_vec = noise_simulator.GetSPEBackground(
            spe_rate, 0, prev_s1_window, prev_s1_window, post_s1_window);
        append_hits(hd, spe_vec);
    } else if (use_data_driven_noise) {
        auto noise_vec = GetDataDrivenNoise(noise_pool, 0, total_wf_length);
        append_hits(hd, noise_vec);
    }

    // sort hits
    // sort_hd(hd);

    // sort and remerge overlap hits
    auto remerged_hits = hit_remerger.remerge_hits(hd.hitsVec);
    hd.hitsVec = remerged_hits;
    sim_events++;
    return hd;
}

// overlay multiple wfs to form a long noise wf
// start time [sample], max_waveform_length [ms]
vector<SingleHit> EventSimulator::GetDataDrivenNoise(EventPool &event_pool,
                                                     uint64_t start_time,
                                                     float max_wf_length) {

    // default method
    /*
    // default noise
    auto event = event_pool.RandomAccess(start_time);
    // noise enhancement
    int n_events = 0;
    while (get_duration_ms(event) < max_wf_length) {
        // 1. calculate next event st
        float signal_den = float(event.signals.size()) / get_duration_ms(event);
        if (event.signals.size() == 1)
            signal_den = 6.8; // default offset
        uint64_t offset = 1.0 / signal_den / 4e-6;
        uint64_t next_event_st = event.signals.back().startTime +
                                 event.signals.back().width + offset;
        // 2. append event
        auto another_event = event_pool.RandomAccess(next_event_st);
        append_event(event, another_event);
        // 3. break if too many events
        n_events++;
        if (n_events > 100) {
            cout << "[GetDataDrivenNoise] append too many events!" << endl;
            break;
        }
    }
    // uniformly shift event in [0, max_wf_length]
    float max_shift = max_wf_length - get_duration_ms(event);
    float shift = rand.Uniform(0, max_shift);
    event_pool.ModifyTime(event, uint64_t(shift / 4e-3));
    // return in vector<SingleHit>
    vector<SingleHit> hits;
    for (auto sig : event.signals) {
        for (auto hit : sig.hits) {
            // push back hits within max waveform length
            if (hit.startTime < uint64_t(max_wf_length / 4e-6))
                hits.push_back(std::move(hit));
        }
        // ignore veto hits, for now
        // for (auto vetoHits: sig) {
        // hits.push_back(std::move(hit));
        // }
    }
    return hits;
    */

    // use this method for 1 ms open-window s1
    vector<PhysicalEventData> pev;
    int max_events = 100;
    for (int i = 0; i < max_events; ++i) {
        auto this_event = event_pool.RandomAccess(0); // new event
        uint64_t event_st = start_time + uint64_t(i * 250 * 1000);
        uint64_t event_shift =
            rand.Uniform(0, 1 - get_duration_ms(this_event)) / 4e-6;
        event_pool.ModifyTime(this_event, event_st + event_shift);
        pev.push_back(std::move(this_event));
        if (float(i + 1) > max_wf_length)
            break;
    }
    vector<SingleHit> hits; // push back hits within max wf length
    for (auto &event : pev) {
        for (auto &sig : event.signals) {
            for (auto &hit : sig.hits) {
                if (hit.startTime < start_time + uint64_t(max_wf_length / 4e-6))
                    hits.push_back(std::move(hit));
            }
            for (auto &hit : sig.vetoHits) {
                if (hit.startTime < start_time + uint64_t(max_wf_length / 4e-6))
                    hits.push_back(std::move(hit));
            }
        }
    }
    sort_hits(hits);
    return hits;
}

// generate a S2 according to x, y, z
HitData EventSimulator::MostCloseGenerate(int electrons, float drift,
                                          uint64_t time_offset, float x,
                                          float y, bool use_paf_pattern) {
    HitData hd;
    vector<SingleHit> vhits;
    if (electrons == 0) {
        hd.runNumber = run;
        hd.groupNumber = group;
        hd.hitsVec = vhits;
        return hd;
    }

    // position simulation
    if (drift == -1)
        drift = rand.Uniform(0, 840);

    // calculate diffusion sigma
    float sigma = sqrt(2 * diffusion_coeff * drift) / 1.411;

    // theta and r: position of simulated event in polar coordinates
    // x and r: position of simulated event in Cartesian coordinates
    float se_pool_range = 40; // this par is crucial for hitStdev and maxQ/S2
    if (abs(most_close_x) < 800 && abs(most_close_y) < 800) {
        x = most_close_x;
        y = most_close_y;
    } else {
        // read x y from input parameter
        // float theta = rand.Uniform(0, 2 * 3.14159);
        // r = sqrt(rand.Uniform(0, 360) * 1e3);
        // x = r * cos(theta);
        // y = r * sin(theta);
    }
    float r = sqrt(x * x + y * y);

    // float range_boost = 525; // for cog cor
    float range_boost = 575; // for cdf paf
    if (r > range_boost) {
        se_pool_range += (r - range_boost);
    }

    // create paf pattern for each (x, y)
    TH1F *h_pattern = nullptr;
    if (use_paf_pattern) {
	// do nothing
    }
    // if (use_paf_pattern) {
    //     gRandom->SetSeed(0); // histogram randomness
    //     h_pattern = new TH1F("h_pattern", "", 200, 0, 200);
    //     double pos[2] = {x, y};
    //     auto etas = paf->GetEtas(pos);
    //     for (auto e : etas) {// pmt no, probability
    //         auto idx = e.first;
    //         auto prob = e.second;
    //         auto ch = pmt_index_map[e.first];
    //         if (prob < 1e-2) {
    //             // continue;
    //             prob *= 0.28;
    //         }
    //         printf("%3d %5d %6.1f %6.1f %8.3e\n", e.first, ch, pmt_map[ch].xpos, pmt_map[ch].ypos, e.second);
    //         h_pattern->Fill(idx, prob);
    //     }
    //     printf("sim pos: %.1f, %.1f\n", x, y);
    //     printf("total prob: %.2f\n", h_pattern->Integral());
    // }

    bool new_method = 1;
    if (new_method) {
        // auto SEs = s2_pool.GetSEsWithinRange(electrons, x, y, drift,
        // time_offset, se_pool_range, sigma);
        auto SEs = s2_pool.GetSEsWithinRange2(
            electrons, x, y, drift, time_offset, se_pool_range, sigma);
        for (auto &se : SEs) {
            // replace channel number for each top hits
            // if (use_paf_pattern) {
            //     printf("SE init: %.f %.f\n", se.fPars.at("xCdfPaf"), se.fPars.at("yCdfPaf"));
            //     // reweight 1
            //     if (0) {
            //         for (auto &hit : se.hits) {
            //             if (pmt_map[hit.channelNumber].pmtarray != "TopMain")
            //                 continue;
            //             int pmt_idx = h_pattern->GetRandom();
            //             hit.channelNumber = pmt_index_map[pmt_idx];
            //         }
            //     }
            //     // reweight 2
            //     if (0) {
            //         for (auto &hit : se.hits) {
            //             if (pmt_map[hit.channelNumber].pmtarray != "TopMain")
            //                 continue;
            //             int n_checks = hit.area;
            //             if (hit.area < 1)
            //                 n_checks = 1;
            //             int max_pmt_idx = 0;
            //             float max_pmt_prob = 0;
            //             // printf("==========\n");
            //             // printf("hit %d %.2f\n", (int)hit.channelNumber,
            //             // hit.area);
            //             for (int i = 0; i < n_checks; ++i) {
            //                 float pmt_idx = h_pattern->GetRandom();
            //                 float pmt_prob = h_pattern->GetBinContent(
            //                     h_pattern->FindBin(pmt_idx));
            //                 // printf("rand: %.2f %d %.2f\n", pmt_idx,
            //                 // (int)pmt_index_map[int(pmt_idx)], pmt_prob);
            //                 if (pmt_prob > max_pmt_prob)
            //                     max_pmt_idx = pmt_idx;
            //             }
            //             hit.channelNumber = pmt_index_map[max_pmt_idx];
            //             // printf("hit modified %d\n", hit.channelNumber);
            //         }
            //     }
            //     // reweight 3
            //     if (1) {
            //         cout << "random test: " << endl;
            //         for (int i = 0; i < 20; ++i) {
            //             float idxf = h_pattern->GetRandom();
            //             int idxi = idxf;
            //             auto chf = pmt_index_map[idxf];
            //             auto chi = pmt_index_map[idxi];
            //             printf("%2d %6.2f %3d %d %d\n", i, idxf, idxi, chf, chi);

            //         }
            //         cout << "max bin: " << h_pattern->GetMaximumBin() << endl;
            //         cout << "max bin: " << h_pattern->GetBinLowEdge(h_pattern->GetMaximumBin()) << endl;
            //         cout << "max bin: " << h_pattern->FindBin(h_pattern->GetMaximumBin()) << endl;

            //         for (auto &hit : se.hits) {
            //             auto chold = hit.channelNumber;
            //             if (1) {
            //                 printf("%12s %d %4.2f %6.1f %6.1f ",
            //                        pmt_map[chold].pmtarray.c_str(),
            //                        hit.channelNumber, hit.area, pmt_map[chold].xpos, pmt_map[chold].ypos);
            //             }

            //             if (pmt_map[hit.channelNumber].pmtarray != "TopMain") {
            //                 printf("\n");
            //                 continue;
            //             }
            //             // int pmt_idx = h_pattern->GetRandom(); // old
            //             float pmt_idx = h_pattern->GetRandom(); // new
            //             // if (hit.area > 2)
            //                 // pmt_idx = h_pattern->FindBin(h_pattern->GetMaximumBin());
            //             auto chnew = pmt_index_map[pmt_idx];
            //             cout << " [" << pmt_idx << " " << chnew <<  "] ";
            //             // float pmt_prob = h_pattern->GetBinContent(
            //                 // h_pattern->FindBin(pmt_idx));
            //                 // printf("rand: %.2f %d %.2f\n", pmt_idx,
            //                 // (int)pmt_index_map[int(pmt_idx)], pmt_prob);
            //             if (0) cout << pmt_idx << endl;
            //             hit.channelNumber = pmt_index_map[pmt_idx];
            //             // printf("hit modified %d\n", hit.channelNumber);
            //             printf("-> %d %6.1f %6.1f", chnew, pmt_map[chnew].xpos, pmt_map[chnew].ypos);
            //             printf("\n");
            //         }
            //     } // reweight 3
            // } // if use paf pattern

            // insert hits
            vhits.insert(vhits.end(), se.hits.begin(), se.hits.end());
        } // for (auto &se : SEs)
    } else {
        // old method
        // for (int i = 0; i < electrons; ++i) {
        //     float offset = rand.Gaus(0, sigma);
        //     auto s2 = s2_pool.GetSignalWithinRange(
        //         x, y, se_pool_range,
        //         uint64_t((drift + offset) / 4e-3) + time_offset);
        //     vhits.insert(vhits.end(), s2.hits.begin(), s2.hits.end());
        // }
    }

    delete h_pattern;

    sort_hits(vhits);
    hd.runNumber = run;
    hd.groupNumber = group;
    hd.hitsVec = std::move(vhits);
    return hd;
}

// randomly generate a S2
HitData EventSimulator::RandomGenerate() {

    HitData hd;
    vector<SingleHit> vhits;

    float drift = rand.Uniform(0, 840);

    // [electron generating method]
    // 1. uniformly from small to large number
    float sim_frac = float(sim_events) / float(total_events);
    int electrons = int(float(max_e - min_e + 1) * sim_frac) + min_e;

    // 2. random sampling in electron range
    // int electrons = (int)rand.Uniform((float)min_e, (float)max_e + 1);

    // [diffusion sigma calculation]
    // electrons = 1;
    // diffusion coeff = 0.0025 mm2 / us
    // velocity        = 1.411 us / mm
    float sigma = sqrt(2.0 * diffusion_coeff * drift) / 1.411;

    for (int i = 0; i < electrons; ++i) {
        float offset = rand.Gaus(0, sigma);
        // cout << "offset: " << offset << endl;
        auto s2 = s2_pool.GetSignal(uint64_t((drift + offset) / 4e-3));
        vhits.insert(vhits.end(), s2.hits.begin(), s2.hits.end());
        // no sort causes double free
        sort_hits(vhits);
    }

    hd.runNumber = run;
    hd.groupNumber = group;
    hd.hitsVec = std::move(vhits);

    return hd;
}

HitData EventSimulator::FixGenerate() {
    HitData hd;
    vector<SingleHit> vhits;

    // position simulation
    float drift = rand.Uniform(0, 840);
    float sigma = sqrt(2 * diffusion_coeff * drift) / 1.411;
    float range = 200;
    float x = fix_x;
    float y = fix_y;

    float sim_frac = float(sim_events) / float(total_events);
    int electrons = int(float(max_e - min_e + 1) * sim_frac) + min_e;

    for (int i = 0; i < electrons; ++i) {
        float offset = rand.Gaus(0, sigma);
        auto s2 = s2_pool.GetSignalWithinRange(
            x, y, range, uint64_t((drift + offset) / 4e-3));
        vhits.insert(vhits.end(), s2.hits.begin(), s2.hits.end());
        sort_hits(vhits);
    }

    hd.runNumber = run;
    hd.groupNumber = group;
    hd.hitsVec = std::move(vhits);
    return hd;
}

HitData EventSimulator::GetDelaySignals(HitData primary_signal) {

    // create empty hit data
    HitData hd;
    hd.runNumber = run;
    hd.groupNumber = 0;
    if (primary_signal.hitsVec.size() == 0)
        return hd;

    if (verbose && 0) {
        cout << "primary_signal size = " << primary_signal.hitsVec.size()
             << " charge: "
             << -accumulate(primary_signal.hitsVec[0].segment.peValue.begin(),
                            primary_signal.hitsVec[0].segment.peValue.end(),
                            0.0)
             << endl;
    }

    vector<SingleHit> input = primary_signal.hitsVec; // first-order input

    vector<SingleHit> delaySignals; // output
    auto concatenate = [&delaySignals](vector<SingleHit> h) {
        delaySignals.insert(delaySignals.end(), h.begin(), h.end());
    };

    int loop = 0; // loop of secondary signals

    // at this stage, just calculate one-loop
    while (loop < 1) {

        // secondary electrons
        vector<SingleHit> secondary_e;

        // loop over hits of input
        for (const auto &hit : input) {

            // hit waveform is the basic element for delay-signal calculation
            const auto &waveform = hit.segment.peValue;

            if (use_afterpulse) {
                vector<pair<uint64_t, float>> AP_arr =
                    ap_simulator.GetAfterPulseArray(hit.channelNumber,
                                                    waveform);
                while (AP_arr.size() != 0) {
                    uint64_t timeAP = AP_arr.front().first;
                    float chargeAP = AP_arr.front().second;

                    HitData spe = s1_simulator.GetScaledSPEHit(
                        hit.startTime + timeAP, chargeAP);

                    AP_arr.erase(AP_arr.begin());
                    concatenate(spe.hitsVec);
                }
            }

            if (use_delayion) {
                vector<uint64_t> SE_arr =
                    di_simulator.GetDelayElectronArray(waveform);
                while (SE_arr.size() != 0) {
                    Signal electron = delay_ion_pool.GetSignal(hit.startTime +
                                                               SE_arr.front());
                    SE_arr.erase(SE_arr.begin());
                    concatenate(electron.hits);
                    // conbine_together(secondary_e, electron.hits);
                }
            }
        }
        // if no secondary signals, break
        // if (secondary_e.size() == 0)
        // break;
        // else
        // input = secondary_e;

        loop++;

        if (verbose) {
            cout << "GetDelaySignals()" << endl;
            cout << "loop: " << loop << endl;
            cout << "size of input: " << input.size() << endl;
        }
    }

    hd.hitsVec = std::move(delaySignals);
    return hd;
}

HitData EventSimulator::G4Generate() {

    cout << "use geant4" << endl;

    HitData hd;
    hd.runNumber = run;
    hd.groupNumber = group;

    HitData hds1 = drop_hit_simulator.GetDroppedSignal(1);
    append_hd(hd, hds1);

    int size = (int)deposition_array.size();
    cout << "deposition_array size: " << size << endl;
    for (int i = 0; i < size; ++i) {
        int electron = 1;
        float drift = deposition_array.at(i) * 10 / 1185 * 840; // cm to us
        cout << "electron: " << i << " / " << size << " "
             << "drift length: " << drift << "\r";
        fflush(stdout);
        HitData hd2 = MostCloseGenerate(electron, drift + drift_g4);
        append_hd(hd, hd2);
    }

    sort_hd(hd);
    sim_events++;
    return hd;
}

int EventSimulator::GetTruthInfoTree(string fname) {

    cout << "Dumping truth info tree..." << endl;
    cout << "Total simulated events: " << sim_events << endl;

    TFile *fout = TFile::Open(fname.c_str(), "recreate");
    TTree *tree = new TTree("truth_tree", "truth info of waveform simulation");
    int photon, electron;
    float drift_time;
    float x, y, r2;
    double qS1True, qS2True;
    uint64_t tS1True, tS2True;

    tree->Branch("photon", &photon);
    tree->Branch("electron", &electron);
    tree->Branch("drift_time", &drift_time);
    tree->Branch("x", &x);
    tree->Branch("y", &y);
    tree->Branch("r2", &r2);
    tree->Branch("qS1True", &qS1True);
    tree->Branch("qS2True", &qS2True);
    tree->Branch("tS1True", &tS1True, "tS1True/l");
    tree->Branch("tS2True", &tS2True, "tS2True/l");

    for (int i = 0; i < sim_events; ++i) {
        photon = truth.photon.at(i);
        electron = truth.electron.at(i);
        drift_time = truth.drift_time.at(i);
        x = truth.x.at(i);
        y = truth.y.at(i);
        r2 = truth.r2.at(i);
        qS1True = truth.qS1True.at(i);
        qS2True = truth.qS2True.at(i);
        tS1True = truth.tS1True.at(i);
        tS2True = truth.tS2True.at(i);
        tree->Fill();
    }

    cout << "Finished." << endl;
    tree->Write();
    fout->Close();

    return 1;
}

HitData EventSimulator::GetQuickS1(uint64_t st) {

    CalibPmtSegment seg;
    seg.startTime = st;
    seg.channelNumber = 11802;
    seg.peValue = {-0.2, -0.4, -0.25, -0.15};

    SingleHit hit;
    hit.channelNumber = seg.channelNumber;
    hit.startTime = seg.startTime;
    hit.peakTime = 1;
    hit.width = 4;
    hit.area = 1;
    hit.height = 0.4;
    hit.preBaseline = 0.01;
    hit.postBaseline = 0.01;
    hit.rmsPreBaseline = 0.01;
    hit.rmsPostBaseline = 0.01;
    hit.hitSearchThreshold = 20;
    hit.type = HitType::NORMAL;
    hit.segment = seg;

    vector<SingleHit> vhit = {hit};

    HitData hd;
    hd.runNumber = run;
    hd.groupNumber = group;
    hd.hitsVec = vhit;
    return hd;
}
