#include <bs3/pbs.hh>

#include <iostream>
#include <exception>

#include "pxtypes.hh"

int main (int argc, char *argv[])
{
    using namespace pbsf;


    if (argc != 2) {
        std::cerr << "Usage: " << argv[0] << " datafile" << std::endl;
        return 1;
    }

    try {
        auto data_file = open_sequential_input_file(argv[1], PandaXIVRealm());
        auto group_data = data_file.read_one_type<GroupData>();
        auto group_count = 0;
        auto n_segments = 0;
        for (const auto &group: group_data) {
            group_count++;
            n_segments += group.segments.size();
        }
        std::cout << n_segments << " segments in " << group_count
                  << " groups." << std::endl;
    } catch (std::exception &e) {
        return 1;
    }
    return 0;
}
