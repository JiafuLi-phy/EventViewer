#include <bs3/pbs.hh>
#include <iostream>
#include <sstream>
#include <string>
#include <unistd.h>

#include "PandaXDataSource.hh"
#include "pxtypes.hh"

#include "json.hpp"

#include "httplib.h"

using std::cerr;
using std::cout;
using std::endl;
using std::istringstream;
using std::ostringstream;
using std::string;

using json = nlohmann::json;

namespace {
std::map<SignalType, std::string> signal_type_mapping{
    {SignalType::S1, "S1"},
    {SignalType::S2, "S2"},
    {SignalType::NOISE, "NOISE"},
    {SignalType::UNKNOWN, "UNKNOWN"},
    {SignalType::SPARKING, "SPARKING"},
    {SignalType::S1_WITH_VETO, "S1_WITH_VETO"},
    {SignalType::S2_WITH_VETO, "S2_WITH_VETO"},
    {SignalType::PMT_SPARKING, "PMT_SPARKING"}};
std::map<HitType, std::string> hit_type_mapping{
    {HitType::NORMAL, "NORMAL"},
    {HitType::NOISE, "NOISE"},
    {HitType::SATURATE, "SATURATE"},
    {HitType::BASELINE, "BASELINE"}};
constexpr auto maxu = std::numeric_limits<uint32_t>::max();
PmtInfoMap pmt_map;
std::string run_start_time;
} // namespace

// convert hit to json format
json hit2json(const SingleHit &hit) {
    json j;
    j["type"] = hit_type_mapping[hit.type];
    j["channelNumber"] = hit.channelNumber;
    j["startTime"] = hit.startTime;
    j["peakTime"] = hit.peakTime;
    j["width"] = hit.width;
    j["area"] = hit.area;
    j["height"] = hit.height;
    return j;
}

// convert the waveform to json format
json segment2json(const CalibPmtSegment &seg) {
    json j;
    j["startTime"] = seg.startTime;
    j["channel"] = seg.channelNumber;
    j["value"] = seg.peValue;
    return j;
}

// convert the signal to json format
json signal2json(const Signal &sig) {
    json j;
    j["type"] = signal_type_mapping[sig.type];
    j["startTime"] = sig.startTime;
    j["endTime"] = sig.endTime;
    j["height"] = sig.height;
    j["charge"] = sig.fPars.at("ChargeTop") + sig.fPars.at("ChargeBottom");
    j["chargeTop"] = sig.fPars.at("ChargeTop");
    j["chargeBottom"] = sig.fPars.at("ChargeBottom");
    for (const auto &hit : sig.hits) {
        j["hits"].push_back(hit2json(hit));
    }
    for (const auto &hit : sig.vetoHits) {
        j["vetoHits"].push_back(hit2json(hit));
    }
    for (const auto &wf : sig.waveform) {
        switch (wf.first) {
        case 90011u:
            j["waveform"] = segment2json(wf.second);
            break;
        case 90012u:
            j["waveformSmear"] = segment2json(wf.second);
            break;
        case 90001u:
            j["waveformBottom"] = segment2json(wf.second);
            break;
        case 90002u:
            j["waveformTop"] = segment2json(wf.second);
            break;
        case 90005u:
            j["waveformVeto"] = segment2json(wf.second);
            break;
        default:
            std::cerr << "unknown waveform channel" << std::endl;
        }
    }
    return j;
}

// convert pmt map to json
json pmt_map2json() {
    json j;
    for (const auto &pmt : pmt_map) {
        json jpmt;
        jpmt["channel_number"] = pmt.second.pmtId;
        jpmt["gain_type"] = pmt.second.gainType;
        jpmt["pmt_type"] = pmt.second.pmtType;
        jpmt["x"] = pmt.second.xpos;
        jpmt["y"] = pmt.second.ypos;
        jpmt["size"] = pmt.second.size;
        jpmt["rotation"] = pmt.second.rotation;
        jpmt["array"] = pmt.second.pmtarray;
        j.push_back(jpmt);
    }
    return j;
}

// convert the physical event to json format
// include the waveform for each signals
json event2json(const PhysicalEventData &event) {
    json j;
    j["runNumber"] = event.runNumber;
    j["eventNumber"] = event.number.eventNumber;
    for (const auto &sig : event.signals) {
        j["signals"].push_back(signal2json(sig));
    }
    j["pmts"] = pmt_map2json();
    j["global_start_time"] = run_start_time;
    return j;
}

template <typename T> void serve_file(const T &file, int port) {

    auto it = file.cbegin();
    using namespace httplib;
    Server svr;

    svr.Get("/", [&](const Request &, Response &res) {
        res.set_content("Hello PandaX!\n", "text/plain");
    });

    svr.Get("/event", [&](const Request &, Response &res) {
        if (it == file.cend()) {
            std::cout << "at file end." << std::endl;
            res.status = 404;
            return;
        }
        std::cout << "serve event " << it->first << std::endl;
        auto event = it->second->template as<PhysicalEventData>();
        auto j = event2json(event);
        res.set_content(j.dump(), "application/json");
    });

    svr.Get(R"(/event/(\d+))", [&](const Request &req, Response &res) {
        uint32_t num;
        {
            std::istringstream ss(req.matches[1]);
            ss >> num;
        }
        if (file.find(num) != file.end()) {
            it = file.find(num);
        } else {
            res.status = 404;
            return;
        }
        std::cout << "serve event " << it->first << std::endl;
        auto event = it->second->template as<PhysicalEventData>();
        auto j = event2json(event);
        res.set_content(j.dump(), "application/json");
    });

    svr.Get("/event/next", [&](const Request &, Response &res) {
        if (it != file.cend())
            ++it;
        if (it == file.cend()) {
            std::cout << "at file end." << std::endl;
            res.status = 404;
            return;
        }
        std::cout << "serve event " << it->first << std::endl;
        auto event = it->second->template as<PhysicalEventData>();
        auto j = event2json(event);
        res.set_content(j.dump(), "application/json");
    });

    svr.Get("/event/previous", [&](const Request &, Response &res) {
        if (it != file.cbegin()) {
            --it;
        } else {
            std::cout << "at file begin." << std::endl;
            res.status = 404;
            return;
        }
        std::cout << "serve event " << it->first << std::endl;
        auto event = it->second->template as<PhysicalEventData>();
        auto j = event2json(event);
        res.set_content(j.dump(), "application/json");
    });

    svr.listen("localhost", port);
}

int main(int argc, char *argv[]) {
    string ipname;
    int port{11180};
    uint32_t n{maxu};
    for (int option; (option = getopt(argc, argv, "i:p:n:")) > 0;) {
        switch (option) {
        case 'i':
            ipname = optarg;
            break;
        case 'p': {
            istringstream ss(optarg);
            ss >> port;
            break;
        }
        case 'n': {
            istringstream ss(optarg);
            ss >> n;
            break;
        }
        default:
            break;
        }
    }
    if (ipname.empty()) {
        cerr << "Usage: " << argv[0]
             << " -i input_pe_name [ -p port_num ] [ -n event_number ]" << endl;
        return 1;
    }

    try {
        auto p_file =
            pbsf::open_indexed_input_file<uint32_t>(ipname, PandaXIVRealm());
        if (p_file.begin() == p_file.end()) {
            cerr << "file is empty" << endl;
            return 1;
        }
        auto run_no = p_file.begin()->second->as<PhysicalEventData>().runNumber;
        {
            PandaXDataSource pds;
            pmt_map = pds.loadPmtMap(run_no);
            run_start_time = pds.loadRunStartTime(run_no);
        }
        if (n != maxu) {
            // we use the input event number to generate the json directly.
            try {
                auto event = p_file[n]->as<PhysicalEventData>();
                auto j = event2json(event);
                std::cout << j << std::endl;
                return 0;
            } catch (pbsf::key_missing_error &e) {
                std::cerr << e.what() << std::endl;
            }
        }
        serve_file(p_file, port);
    } catch (std::exception &e) {
        std::cerr << e.what() << std::endl;
    }
    return 0;
}
