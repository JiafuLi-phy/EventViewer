#include "EventPool.hh"
EventPool::EventPool() { rand.SetSeed(0); }

namespace pu = pbsu;
namespace pf = pbsf;

// load event from indexed pe data
void EventPool::LoadPool(string ifname, int max_size) {

    auto data_file =
        pf::open_indexed_input_file<EventIndex>(ifname, PandaXIVRealm());

    printf("Event pool name: %s\n", ifname.c_str());
    printf("Event pool size: %d, ", (int)data_file.size());
    printf("required: %d\n", max_size);

    auto data_file_start = data_file.begin();
    // read from middle of iterator
    if (max_size != -1) {
        int shift = rand.Uniform(0, float(data_file.size()) - float(max_size));
        for (int i = 0; i < shift; ++i) {
            data_file_start++;
        }
    }

    int data_size = 0;
    for (auto it = data_file_start; it != data_file.end(); ++it) {
        const auto &idx = it->first;
        const auto &pd = it->second->as<PhysicalEventData>();
        event_index.push_back(std::move(idx));
        event_pool.push_back(std::move(pd));
        ++data_size;
        if (data_size % 100 == 0) {
            printf("size: %d / %d\r", data_size, max_size);
            fflush(stdout);
        }
        if (max_size != -1 && data_size == max_size) {
            break;
        }
    }
    printf("Event pool size: %d     \n", data_size);
}

// for ac simulation
// load event charge in [min, max] with iterator
// percent is for template-level division
// e.g. percent [0,5] means read event 0,1,2,3,4,5 for every 10 events
void EventPool::LoadPoolInRange(string ifname, int max_size, float min,
                                float max, int percent_min, int percent_max) {
    auto data_file =
        pf::open_indexed_input_file<EventIndex>(ifname, PandaXIVRealm());

    printf("Event pool name: %s\n", ifname.c_str());
    printf("Event pool size: %d, ", (int)data_file.size());
    printf("required: %d\n", max_size);
    printf("charge range: [%.1f, %.1f]\n", min, max);
    printf("percent: [%d, %d]\n", percent_min, percent_max);

    auto get_charge = [](const PhysicalEventData &pd) {
        float q = 0;
        for (auto sig : pd.signals) {
            q += sig.fPars.at("Charge");
        }
        return q;
    };

    int data_size = 0;
    auto data_file_start = data_file.begin();
    int location = -1;
    for (auto it = data_file_start; it != data_file.end(); ++it) {
        ++location; // start from 0
        const auto &idx = it->first;
        const auto &pd = it->second->as<PhysicalEventData>();
        // int percent = location % 10;
        int percent = pd.number.eventNumber % 10;
        if (!(percent_min <= percent && percent <= percent_max)) {
            continue;
        }
        auto q_event = get_charge(pd);
        if (q_event < min || q_event > max) {
            continue;
        }
        event_index.push_back(std::move(idx));
        event_pool.push_back(std::move(pd));
        ++data_size;
        printf("size: %d / %d\r", data_size, location);
        fflush(stdout);
        if (max_size != -1 && data_size == max_size) {
            break;
        }
    }
    printf("Event pool size: %d     \n", data_size);
}

// random access event with given time
PhysicalEventData EventPool::RandomAccess(int time) {
    if (event_pool.size() == 0) {
        cout << "[EventPool] event pool empty!" << endl;
    }
    int event_i = rand.Uniform(0, event_pool.size());
    index_stored = event_i;
    auto event_out = event_pool.at(event_i);
    if (time != -1) {
        ModifyTime(event_out, uint64_t(time));
        return event_out;
    }
    return event_out;
}

// random access event with required drift time
PhysicalEventData EventPool::RandomAccessForS1max(float drift_time_us) {
    // we want to control time of s1max in the event
    if (drift_time_us < 0 || drift_time_us > 1000) {
        cout << "[EventPool] invalid drift time." << endl;
        return RandomAccess(0);
    }

    int max_search = 100; // typical search: 5
    for (int i = 0; i < max_search; ++i) {
        // 1. access event with st = 0
        auto pd = RandomAccess(0);

        // 2. calculate index of s1max
        int iS1_max = find_s1_max(pd);
        if (iS1_max == -1) {
            // cout << "no s1 max. next signal" << endl;
            continue;
        }

        // 3. calculate necessary parameters
        uint64_t tS1_max = pd.signals[iS1_max].startTime;
        uint64_t duration_sample = pd.signals.back().startTime +
                                   pd.signals.back().width -
                                   pd.signals.front().startTime;
        float duration_us = float(duration_sample) * 4e-3;
        float tS1_max_in_signals =
            float(tS1_max - pd.signals.front().startTime) * 4e-3; // us

        // // 4. debug code
        // printf("drift time required: %.2f [us]\n", drift_time_us);
        // printf("duration: %.2f\n", duration_us);
        // printf("total signals: %d\n", (int)pd.signals.size());
        // printf("iS1_max: %d\n", iS1_max);
        // printf("\n");

        // 5. we search for pd that in [0, 1000] us, wherever s1max is aligned.
        bool left_safe = drift_time_us > tS1_max_in_signals;
        bool right_safe =
            (duration_us + drift_time_us - tS1_max_in_signals) < 1000;
        if (left_safe && right_safe) {
            ModifyTime(pd,
                       uint64_t(250 * (drift_time_us - tS1_max_in_signals)));
            return pd;
        }
    }

    cout << "[EventPool::RandomAccessForS1max] max search!" << endl;
    return RandomAccess(0);
}

// find index of s1max in signals, same as PeRoot.cc
int find_s1_max(PhysicalEventData &pd) {
    auto &signals = pd.signals;
    int iS1_max = -1;
    float qS1_max = 0;
    for (int i = 0; i < (int)signals.size(); ++i) {
        if (signals[i].type != SignalType::S1 &&
            signals[i].type != SignalType::S1_WITH_VETO) {
            continue;
        }
        uint64_t dt_prev, dt_next;
        float q_prev, q_next;
        if (i == 0) {
            dt_prev = std::numeric_limits<uint64_t>::max();
            q_prev = 0;
        } else {
            dt_prev = signals[i].startTime - signals[i - 1].startTime -
                      signals[i - 1].width;
            q_prev = signals[i - 1].fPars.at("ChargeTop") +
                     signals[i - 1].fPars.at("ChargeBottom");
        }
        if (i == (int)signals.size() - 1) {
            dt_next = std::numeric_limits<uint64_t>::max();
            q_next = 0;
        } else {
            dt_next = signals[i + 1].startTime - signals[i].startTime -
                      signals[i].width;
            q_next = signals[i + 1].fPars.at("ChargeTop") +
                     signals[i + 1].fPars.at("ChargeBottom");
        }
        float charge = signals[i].fPars.at("ChargeTop") +
                       signals[i].fPars.at("ChargeBottom");
        bool large = charge > qS1_max;
        bool clean = (dt_prev > 100 || charge > 3 * q_prev) &&
                     (dt_next > 100 || charge > 3 * q_next);
        // auto &sig = signals[i];
        // printf("q: %.2f t: %.2f type: %d t2next: %.2f qS1_max: %.2f ",
        // sig.fPars.at("Charge"), float(sig.startTime -
        // pd.signals.front().startTime) * 4e-3, (int)sig.type, float(dt_next) *
        // 4e-3, qS1_max); cout << "large: " << large << " clean: " << clean <<
        // endl;
        if (large && clean) {
            qS1_max = charge;
            iS1_max = i;
        }
    }
    // cout << "find_s1_max iS1_max: " << iS1_max << endl;
    return iS1_max;
}

// modify event to an absolute start time
void EventPool::ModifyTime(PhysicalEventData &event, uint64_t time) {
    auto t0 = event.signals.front().startTime;
    for (auto &sig : event.signals) {
        auto tsig = sig.startTime;
        ModifyTime(sig, time + tsig - t0);
    }
}

void EventPool::ModifyTime(Signal &signal, uint64_t time) {
    auto t0 = signal.startTime;
    auto t1 = time;
    if (t0 >= t1) {
        auto offset = t0 - t1;
        signal.startTime -= offset;
        for (auto &wf : signal.waveform) {
            wf.second.startTime -= offset;
        }
        for (auto &hit : signal.hits) {
            hit.startTime -= offset;
            hit.segment.startTime -= offset;
        }
    } else {
        auto offset = t1 - t0;
        signal.startTime += offset;
        for (auto &wf : signal.waveform) {
            wf.second.startTime += offset;
        }
        for (auto &hit : signal.hits) {
            hit.startTime += offset;
            hit.segment.startTime += offset;
        }
    }
}
