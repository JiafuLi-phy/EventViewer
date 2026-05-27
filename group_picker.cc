#include <bs3/pbs.hh>
#include <sys/stat.h>
#include <unistd.h>

#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#include "pxtypes.hh"

using std::ifstream;
using std::istringstream;
using std::map;
using std::string;
using std::vector;

string get_full_file_name(const string &directory, uint32_t run,
                          uint32_t file) {
    std::ostringstream oss;
    oss << directory;
    auto n1k = run / 1000 * 1000;
    oss << "/" << n1k << "/" << run << "/group_run" << std::setw(5)
        << std::setfill('0') << run << "_file" << std::setw(5)
        << std::setfill('0') << file << ".bsd";
    return oss.str();
}

int main(int argc, char *argv[]) {
    string directory{"/store/pandax/group_data"}, ofname{"group_out.bsd"}, suffix{"all"},
        lfname{"event_list.txt"}, output_dir{"."};
    uint32_t run{0};
    for (int option; (option = getopt(argc, argv, "d:r:l:o:s:")) > 0;) {
        switch (option) {
        case 'd':
            directory = optarg;
            break;
        case 's':
	    suffix = optarg;
	    break;
        case 'r': {
            istringstream iss{optarg};
            iss >> run;
            std::ostringstream oss;
            oss << "group_run" << std::setw(5) << std::setfill('0') << run
                << "_selected.bsd";
            ofname = oss.str();
        } break;
        case 'l':
            lfname = optarg;
            break;
        case 'o':
            output_dir = optarg;
            break;
        default:
            break;
        }
    }
    if (run == 0) {
        std::cerr << "Please provide run number with the \"-r\" option.\n";
        return 1;
    }
    if (suffix != "all"){
    suffix = "_" + suffix + ".bsd";
    ofname = output_dir + "/" + ofname.substr(0, ofname.length()-4)  + suffix; 
    }
    else
    ofname = output_dir + "/" + ofname;
    namespace pu = pbsu;
    namespace pf = pbsf;

    // read the input file
    // file format: run file event start_time end_time
    ifstream iff{lfname};
    uint32_t run_number, file_number, event_number;
    uint64_t start_time, end_time;

    using event_time_tuple = std::tuple<uint32_t, uint64_t, uint64_t>;
    map<uint32_t, vector<event_time_tuple>> ft_map;
    while (iff >> run_number >> file_number >> event_number >> start_time >>
           end_time) {
        if (run_number != run)
            continue;
        if (ft_map.find(file_number) == ft_map.end()) {
            vector<event_time_tuple> pt = {
                std::make_tuple(event_number, start_time, end_time)};
            ft_map.emplace(file_number, std::move(pt));
        } else {
            ft_map[file_number].emplace_back(event_number, start_time,
                                             end_time);
        }
    }
    if (ft_map.empty()) {
        std::cerr << "The given run " << run << " is not found in the list.\n";
        return 1;
    }
    auto outfile =
        pbsf::open_indexed_output_file<EventIndex>(ofname, PandaXIVRealm());

    // loop over map, open files and pick groups
    struct stat buffer;
    uint32_t group_number{0};
    for (const auto &ft : ft_map) {
        file_number = ft.first;
        std::cout << "file " << file_number << "..." << std::endl;
        auto ifname = get_full_file_name(directory, run, file_number);
        if (stat(ifname.c_str(), &buffer) != 0) {
            std::cout << "file " << ifname << " does not exist!" << std::endl;
            continue;
        }
        auto vt = ft.second;
        // sort the input entry
        std::sort(vt.begin(), vt.end(), [](const auto &a, const auto &b) {
            return std::get<0>(a) < std::get<0>(b);
        });
        try {
            auto data_file =
                open_sequential_input_file(ifname, PandaXIVRealm());
            auto g_data = data_file.read_one_type<GroupData>();
            auto it = vt.begin();
            if (it == vt.end())
                continue;
            auto est = std::get<1>(*it);
            auto eet = std::get<2>(*it);
            event_number = std::get<0>(*it);
            vector<RawPmtSegment> segs;
            uint64_t ss_st{0}, ss_et{0};
            for (const auto &group : g_data) {
            GROUP_BEHIND:
                if (group.startTime > eet) {
                    // group is behind the event
                    // create group when possible
                    if (!segs.empty()) {
                        GroupData gd{run, group_number, ss_st, ss_et, segs};
                        EventIndex idx{run, file_number, event_number};
                        outfile.insert(std::make_tuple(idx, std::move(gd)));
                        std::cout << "picked from file " << file_number
                                  << " with event number " << event_number
                                  << std::endl;
                        segs.clear();
                    }
                    ++it;
                }
                if (it == vt.end()) {
                    break;
                }
                est = std::get<1>(*it);
                eet = std::get<2>(*it);
                event_number = std::get<0>(*it);

                // group is a head of the event
                // skip group
                if (group.endTime < est)
                    continue;

                // if the group is still behind the event, recheck it.
                if (group.startTime > eet) {
                    goto GROUP_BEHIND;
                }
                // loop over all segments in the group, sort first
                auto segments = group.segments;
                std::sort(segments.begin(), segments.end(),
                          [](const auto &a, const auto &b) {
                              return a.startTime < b.startTime;
                          });

                for (const auto &seg : segments) {
                    auto seg_et = seg.startTime + seg.adcValue.size();
                    // segment is behind the event
                SEG_BEHIND:
                    if (seg.startTime > eet) {
                        if (!segs.empty()) {
                            GroupData gd{run, group_number, ss_st, ss_et, segs};
                            EventIndex idx{run, file_number, event_number};
                            outfile.insert(std::make_tuple(idx, std::move(gd)));
                            std::cout << "picked from file " << file_number
                                      << " with event number " << event_number
                                      << std::endl;
                            segs.clear();
                        }
                        ++it;
                        if (it == vt.end())
                            break;
                        est = std::get<1>(*it);
                        eet = std::get<2>(*it);
                        event_number = std::get<0>(*it);
                    }

                    // segment is ahead of the event, skip it
                    if (seg_et < est)
                        continue;

                    // segment is overlapped with the event, use it
                    // update the start and end time of the group.
                    if (seg.startTime <= eet) {
                        if (seg.startTime < ss_st || ss_st == 0)
                            ss_st = seg.startTime;
                        if (seg_et > ss_et)
                            ss_et = seg_et;
                        segs.push_back(seg);
                        continue;
                    }

                    // segment is behind the current event, recheck
                    goto SEG_BEHIND;
                }
                if (it == vt.end())
                    break;
            }
            if (!segs.empty()) {
                GroupData gd{run, group_number, ss_st, ss_et, segs};
                EventIndex idx{run, file_number, event_number};
                outfile.insert(std::make_tuple(idx, std::move(gd)));
                std::cout << "picked from file " << file_number
                          << " with event number " << event_number << std::endl;
            }
        } catch (std::exception &e) {
            std::cerr << "error in " << ifname << std::endl;
            std::cerr << e.what() << std::endl;
        }
    }
}
