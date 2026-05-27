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

int main(int argc, char *argv[]) {
    string ifname;
    for (int option; (option = getopt(argc, argv, "i:")) > 0;) {
        switch (option) {
        case 'i':
            ifname = optarg;
            break;
        default:
            break;
        }
    }
    if (ifname.empty()) {
        cerr << "Usage: " << argv[0] << " -i input_file" << endl;
        return 1;
    }
    namespace pu = pbsu;
    namespace pf = pbsf;

    auto data_file = open_sequential_input_file(ifname, PandaXIVRealm());
    auto event_data = data_file.read_one_type<PhysicalEventData>();
    for (const auto &event: event_data) {
        cout << "+++ event ";
        cout << event.number.eventNumber << endl;
        cout << event.signals.size() << " signals" << endl;
        auto dt = (event.signals.back().endTime - event.signals.front().startTime)/100;
        cout << "start from " << event.signals.front().startTime
             << " to " << event.signals.back().endTime << " ("
             << dt << " us)" << endl << endl;
    }
}
