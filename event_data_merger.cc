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
        << std::setfill('0') << file << "_fpe.bsd";
    return oss.str();
}

int main(int argc, char *argv[]) {
    string directory{"/data/user/pandax/pe_data"}, ofname{"event_mpe.bsd"},
        lfname{"event_list.txt"};
    bool append{false};
    for (int option; (option = getopt(argc, argv, "d:o:l:a")) > 0;) {
        switch (option) {
        case 'd':
            directory = optarg;
            break;
        case 'o':
            ofname = optarg;
            break;
        case 'l':
            lfname = optarg;
            break;
        case 'a':
            append = true;
        default:
            break;
        }
    }
    namespace pu = pbsu;
    namespace pf = pbsf;

    // read the input file

    ifstream iff{lfname};
    uint32_t run_number, file_number, event_number;

    // file_number -> [event_number]
    using fe_map = map<uint32_t, vector<uint32_t>>;

    // run_number -> fe_map
    using run_map = map<uint32_t, fe_map>;

    run_map rmap;
    while (iff >> run_number >> file_number >> event_number) {
        if (rmap.find(run_number) == rmap.end()) {
            fe_map fm{{file_number, {event_number}}};
            rmap.emplace(run_number, std::move(fm));
        } else {
            auto &m_entry = rmap[run_number];
            if (m_entry.find(file_number) == m_entry.end()) {
                vector<uint32_t> el = {event_number};
                m_entry.emplace(file_number, std::move(el));
            } else {
                m_entry[file_number].push_back(event_number);
            }
        }
    }

    // open the output file for write.
    auto outfile = pbsf::open_indexed_output_file<EventIndex>(
        ofname, PandaXIVRealm(), !append);

    // loop the input files
    struct stat buffer;
    for (const auto &r : rmap) {
        std::cout << "run " << r.first << "..." << std::endl;
        for (const auto &f : r.second) {
            std::cout << "file " << f.first << "..." << std::endl;
            // construct the file name.
            auto ifname = get_full_file_name(directory, r.first, f.first);
            if (stat(ifname.c_str(), &buffer) != 0) {
                std::cout << "file " << ifname << " does not exist!"
                          << std::endl;
                continue;
            }
            std::cout << "file name: " << ifname << std::endl;
            try {
                auto ifile = pbsf::open_indexed_input_file<uint32_t>(
                    ifname, PandaXIVRealm());
                for (const auto &ei : f.second) {
                    EventIndex idx{r.first, f.first, ei};
                    // the event is already exist in the file
                    if (outfile.find(idx) != outfile.end())
                        continue;
                    auto it = ifile.find(ei);
                    if (it != ifile.end()) {
                        auto event = it->second->as<PhysicalEventData>();
                        outfile.insert(std::make_tuple(idx, event));
                    }
                }
            } catch (std::exception &e) {
                std::cerr << "error in " << ifname << std::endl;
                std::cerr << e.what() << std::endl;
            }
        }
    }
}
