#include "TFile.h"
#include "TH1F.h"
#include "TString.h"
#include "TTree.h"
#include <bs3/pbs.hh>
#include <iostream>
#include <map>
#include <pxtypes.hh>
#include <sstream>
#include <string>
#include <unistd.h>

using std::string;
using std::cout;
using std::endl;
using std::cerr;
using std::map;

float fill_wf_to_histogram(TH1F &histo, const CalibPmtSegment &seg, uint64_t start_time) {
    float min_v = 0.0f;
    auto st = seg.startTime - start_time + 100;
    for (const auto &v: seg.peValue) {
        histo.SetBinContent(++st, v);
        min_v = std::min(min_v, v);
    }
    return min_v;
}

int main(int argc, char *argv[]) {
    string ifname, ofname("event.root");
    uint32_t event_number(0);
    for (int option; (option = getopt(argc, argv, "i:n:o:")) > 0;) {
        switch (option) {
        case 'i':
            ifname = optarg;
            break;
        case 'n':
            event_number = atoi(optarg);
            break;
        case 'o':
            ofname = optarg;
            break;
        default:
            break;
        }
    }
    if (ifname.empty()) {
        cerr << "Usage:" << argv[0]
             << " -i input_name -n event_number -o output_name" << endl;
        return 1;
    }
    namespace pu = pbsu;
    namespace pf = pbsf;

    auto data_file = open_sequential_input_file(ifname, PandaXIVRealm());
    auto event_data = data_file.read_one_type<PhysicalEventData>();

    auto ei = event_data.begin();
    auto run = event_data.begin()->runNumber;
    while (ei != event_data.end()) {
        if (ei->number.eventNumber != event_number) {
            ei++;
            continue;
        }
        cout << "found event id " << event_number << "." << endl;
        cout << "found " << ei->signals.size() << " signals." << endl;
        const auto &signals = ei->signals;
        auto dt = signals.back().endTime - signals.front().startTime + 200;
        cout << "dt = " << dt/100 << "us (" << signals.front().startTime << " - " << signals.back().endTime << ")." << endl;
        TFile fout(ofname.c_str(), "RECREATE");
        TH1F t_all ("wf", Form("Event Waveform, run %d event %d", run, event_number), int(dt), 0.0, double(dt));
        TH1F t_top ("wf_top", Form("Event Waveform Top, run %d event %d", run, event_number), int(dt), 0.0, double(dt));
        TH1F t_bottom ("wf_bottom", Form("Event Waveform Bottom, run %d event %d", run, event_number), int(dt), 0.0, double(dt));
        auto min_v_all = 0.0f;
        auto min_v_top = 0.0f;
        auto min_v_bottom = 0.0f;
        auto start_time = signals.front().startTime;
        for (const auto &sig: signals) {
            auto wf = sig.waveform.find(90011);
            if ( wf == sig.waveform.end()) {
                cerr << "warning: no esum waveform for signal " << endl;
                continue;
            }
            min_v_all = std::min(min_v_all, fill_wf_to_histogram(t_all, wf->second, start_time));
            wf = sig.waveform.find(90002);
            if (wf != sig.waveform.end()) {
                min_v_top = std::min(min_v_top, fill_wf_to_histogram(t_top, wf->second, start_time));
            }
            wf = sig.waveform.find(90001);
            if (wf != sig.waveform.end()) {
                min_v_bottom = std::min(min_v_bottom, fill_wf_to_histogram(t_bottom, wf->second, start_time));
            }            
        }
        t_all.SetMinimum(min_v_all * 1.1);
        t_all.SetLineColor(2);
        t_all.Write();
        t_top.SetMinimum(min_v_top * 1.1);
        t_top.SetLineColor(4);
        t_top.Write();
        t_bottom.SetMinimum(min_v_bottom * 1.1);
        t_bottom.SetLineColor(8);
        t_bottom.Write();
        break;
    }
}
