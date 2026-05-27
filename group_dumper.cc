#include <bs3/pbs.hh>

#include <iostream>
#include <sstream>

#include "pxtypes.hh"

int main (int argc, char *argv[])
{
    using namespace pbsf;

    using std::cout;
    using std::cerr;
    using std::endl;

    if (argc != 3) {
        cerr << "Usage: " << argv[0] << " datafile group_number" << endl;
        return 1;
    }

    unsigned int max_group_number;

    {
        std::stringstream ss(argv[2]);
        ss >> max_group_number;
    }

    auto data_file = open_sequential_input_file(argv[1], PandaXIVRealm());
    auto group_data = data_file.read_one_type<GroupData>();
    for (const auto &cluster: group_data) {
        if (cluster.groupNumber == max_group_number) {
            cout << "cluster " << cluster.groupNumber << " has "
                 << cluster.segments.size() << " segments." << endl;
            cout << "[" << cluster.startTime << ", " << cluster.endTime << "]" << endl;
            for (const auto &seg : cluster.segments) {
                cout << seg.channelNumber << ": (" << seg.startTime << ", "
                     << seg.startTime + seg.adcValue.size() << ")" << endl;
            }
            break;
        }
	//        cout << cluster.groupNumber << endl;
    }
}
