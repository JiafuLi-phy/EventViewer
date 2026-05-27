#include <iostream>
#include <unistd.h>

#include <EventSelector.hh>

using namespace std;

int main(int argc, char *argv[]) {

    string i_fName, mapping_fName, TMcor_fName, elifetime_fName, xml_fName,
        o_fName{"ana_out.root"},
        pol_fName{"/store/user/bozihao/mapfiles/pol_ranks.txt"};
    bool store_whole_data_flag{false};
    bool store_array{false};
    bool is_TM_cor{false};

    for (int option; (option = getopt(argc, argv, "i:m:t:e:x:o:u:sa")) > 0;) {
        switch (option) {
        case 'i':
            i_fName = optarg;
            break;
        case 'm':
            mapping_fName = optarg;
            break;
        case 't':
            TMcor_fName = optarg;
            break;
        case 'e':
            elifetime_fName = optarg;
            break;
        case 'x':
            xml_fName = optarg;
            break;
        case 'o':
            o_fName = optarg;
            break;
        case 'u':
            pol_fName = optarg;
            break;
        case 's':
            store_whole_data_flag = true;
            break;
        case 'a':
            store_array = true;
            break;
        default:
            break;
        }
    }
    if (i_fName.empty() || mapping_fName.empty() || o_fName.empty()) {
        cerr << "Usage:" << argv[0]
             << " -i input_pe_root_file -m mapping_file -t TMcor_file -e "
                "elifetime_file -x xml_file -o output_file [-s -a]"
             << endl;
        return 1;
    }

    auto *es =
        new EventSelector(i_fName, elifetime_fName, mapping_fName, pol_fName, TMcor_fName, xml_fName);
    
    es->SetDeadtimeNScaleFactor(50);

    es->LoadMappingFile();
    es->LoadPolRankFile();
    es->LoadElectronLifetime();
    if (!TMcor_fName.empty()) {
        is_TM_cor = es->LoadTMcorFile();
    }
    es->SetOutputName(o_fName.c_str());
    es->OpenOutputRootFile();
    es->CreateBranches();
    if (store_array) {
        es->CreateArrayBranches();
    }
    if (!xml_fName.empty()) {
        es->CreateBDTBranch();
        es->CreateBDTReader();
    }

    es->ReadPeTree();
    std::cout << "Processing..." << std::endl;
    for (int i = 0; i < es->GetPeEntries(); ++i) {
        es->GetPeEntry(i);
        es->SetPeOutputTreeValue();
        if (store_array) {
            es->SetPeOutputTreeArray();
        }
        if (es->ApplyQualityCut(store_whole_data_flag))
            continue;
        if (store_array) {
            es->SetArrayCorrectCharge();
            es->SetArrayCorrectCharge_Unbin();
        } else {
            es->SetCorrectCharge();
            es->SetCorrectCharge_Unbin();
            es->StretchS1S2();
        }
        if (is_TM_cor) {
            es->SetCorrectTMs();
        }
        if (!xml_fName.empty())
            es->EvaluateBDT();
        es->FillPeOutputTree();
    }

    es->WritePeOutputTree();
    es->CloseOutputFile();
    cout << o_fName << " finished\n";
}
