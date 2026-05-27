#include "EventSelector.hh"
#include <TChain.h>
#include <TFileCollection.h>

using namespace TMVA;
EventSelector::EventSelector(const string &i_fName,
                             const string &elifetime_fName,
                             const string &mapping_fName,
                             const string &polrank_fName,
                             const string &TMcor_fName,
                             const string &xml_fName) {

    mapping_file_name = mapping_fName.c_str();
    if (mapping_fName.find("PAF") != mapping_fName.npos) {
        if (mapping_fName.find("cdfPAF") != mapping_fName.npos)
            use_cdfPAF_mapping = true;
        else
            use_PAF_mapping = true;
    } else {
        if (mapping_fName.find("cdfTMs") != mapping_fName.npos)
            use_cdfTMs_mapping = true;
        else
            use_TMs_mapping = true;
    }
    polrank_file_name = polrank_fName.c_str();
    TMcor_file_name = TMcor_fName.c_str();
    elifetime_file_name = elifetime_fName.c_str();
    xml_file_name = xml_fName.c_str();

    auto *ch = new TChain("event_tree");
    ch->Add(i_fName.c_str());
    o_runNumber = std::stoi(i_fName.substr(i_fName.find("group_run") + 9, 5));
    fReaderPe = new TTreeReader(ch);
    adaptive_deadtime_cut.SetInputPeRootFile(i_fName);
    adaptive_deadtime_cut.CalculateSilentSignalRate();
    deadtime_scale_factor = -1;
    cout << "Event selector initialized." << endl;
}

void EventSelector::SetDeadtimeScaleFactor(int scale_factor) { deadtime_scale_factor = scale_factor; }

void EventSelector::SetDeadtimeNScaleFactor(int n_scale_factor) { adaptive_deadtime_cut.SetNScaleFactor(n_scale_factor); }

EventSelector::~EventSelector() = default;

void EventSelector::SetOutputName(const char *name) { o_fName = name; }

void EventSelector::OpenOutputRootFile() {
    o_file = new TFile(o_fName.Data(), "RECREATE");
}

Long64_t EventSelector::GetPeEntries() { return fReaderPe->GetEntries(); }

void EventSelector::GetPeEntry(int i) { fReaderPe->SetEntry(i); }

void EventSelector::ReadPeTree() {

    runNumber = {*fReaderPe, "runNumber"};
    fileNumber = {*fReaderPe, "fileNumber"};
    eventNumber = {*fReaderPe, "eventNumber"};
    type = {*fReaderPe, "type"};
    t = {*fReaderPe, "t"};
    iS1_max = {*fReaderPe, "iS1_max"};
    iS1_max_charge_pairing = {*fReaderPe, "iS1_max_charge_pairing"};
    iRealS1_max_charge_pairing = {*fReaderPe, "iRealS1_max_charge_pairing"};
    nCandidateS1 = {*fReaderPe, "nCandidateS1"};
    iS2_max = {*fReaderPe, "iS2_max"};
    tS1_max = {*fReaderPe, "tS1_max"};
    tS1_max_charge_pairing =  {*fReaderPe, "tS1_max_charge_pairing"};
    tS2_max = {*fReaderPe, "tS2_max"};
    hS1_max = {*fReaderPe, "hS1_max"};
    hS1_max_charge_pairing = {*fReaderPe, "hS1_max_charge_pairing"};
    hS2_max = {*fReaderPe, "hS2_max"};
    wS1_max = {*fReaderPe, "wS1_max"};
    wS1_max_charge_pairing = {*fReaderPe, "wS1_max_charge_pairing"};
    wS2_max = {*fReaderPe, "wS2_max"};
    qS1_max = {*fReaderPe, "qS1_max"};
    qS1_max_charge_pairing = {*fReaderPe, "qS1_max_charge_pairing"};
    qS2_max = {*fReaderPe, "qS2_max"};
    qS1T_max = {*fReaderPe, "qS1T_max"};
    qS1B_max = {*fReaderPe, "qS1B_max"};
    qS2T_max = {*fReaderPe, "qS2T_max"};
    qS2B_max = {*fReaderPe, "qS2B_max"};
    xS1T_max = {*fReaderPe, "xS1T_max"};
    yS1T_max = {*fReaderPe, "yS1T_max"};
    xS1B_max = {*fReaderPe, "xS1B_max"};
    yS1B_max = {*fReaderPe, "yS1B_max"};
    xS2T_max = {*fReaderPe, "xS2T_max"};
    yS2T_max = {*fReaderPe, "yS2T_max"};
    xS2B_max = {*fReaderPe, "xS2B_max"};
    yS2B_max = {*fReaderPe, "yS2B_max"};
    xS1Tcor_max = {*fReaderPe, "xS1Tcor_max"};
    yS1Tcor_max = {*fReaderPe, "yS1Tcor_max"};
    xS1Bcor_max = {*fReaderPe, "xS1Bcor_max"};
    yS1Bcor_max = {*fReaderPe, "yS1Bcor_max"};
    xS2Tcor_max = {*fReaderPe, "xS2Tcor_max"};
    yS2Tcor_max = {*fReaderPe, "yS2Tcor_max"};
    xS2Bcor_max = {*fReaderPe, "xS2Bcor_max"};
    yS2Bcor_max = {*fReaderPe, "yS2Bcor_max"};
    qSparking = {*fReaderPe, "qSparking"};
    qPMTSparking = {*fReaderPe, "qPMTSparking"};
    //    qNoise = {*fReaderPe, "qNoise"};
    qUnknown = {*fReaderPe, "qUnknown"};
    qOthers = {*fReaderPe, "qOthers"};
    nS1 = {*fReaderPe, "nS1"};
    nS2 = {*fReaderPe, "nS2"};
    nPMTSparking = {*fReaderPe, "nPMTSparking"};
    nSparking = {*fReaderPe, "nSparking"};
    nNoise = {*fReaderPe, "nNoise"};
    nUnknown = {*fReaderPe, "nUnknown"};
    nOthers = {*fReaderPe, "nOthers"};
    tS1 = {*fReaderPe, "tS1"};
    tS2 = {*fReaderPe, "tS2"};
    qS1 = {*fReaderPe, "qS1"};
    qS1Veto = {*fReaderPe, "qS1Veto"};
    qS1VetoT = {*fReaderPe, "qS1VetoT"};
    qS1VetoB = {*fReaderPe, "qS1VetoB"};
    qS1Tenth = {*fReaderPe, "qS1Tenth"};
    qS1FWHM1 = {*fReaderPe, "qS1FWHM1"};
    qS1FWHM2 = {*fReaderPe, "qS1FWHM2"};
    qS1FWHM3 = {*fReaderPe, "qS1FWHM3"};
    qS2 = {*fReaderPe, "qS2"};
    qS2Tenth = {*fReaderPe, "qS2Tenth"};
    qS2FWHM1 = {*fReaderPe, "qS2FWHM1"};
    qS2FWHM2 = {*fReaderPe, "qS2FWHM2"};
    qS2FWHM3 = {*fReaderPe, "qS2FWHM3"};
    qS1T = {*fReaderPe, "qS1T"};
    qS1B = {*fReaderPe, "qS1B"};
    qS2T = {*fReaderPe, "qS2T"};
    qS2B = {*fReaderPe, "qS2B"};
    hS1 = {*fReaderPe, "hS1"};
    hS2 = {*fReaderPe, "hS2"};
    wS1 = {*fReaderPe, "wS1"};
    wS2 = {*fReaderPe, "wS2"};
    widthTenS1 = {*fReaderPe, "widthTenS1"};
    widthTenS2 = {*fReaderPe, "widthTenS2"};
    wS1FWHM = {*fReaderPe, "wS1FWHM"};
    wS2FWHM = {*fReaderPe, "wS2FWHM"};
    wS1CDF = {*fReaderPe, "wS1CDF"};
    wS1CDF5 = {*fReaderPe, "wS1CDF5"};
    wS1CDF10 = {*fReaderPe, "wS1CDF10"};
    wS1CDF25 = {*fReaderPe, "wS1CDF25"};
    wS1CDF50 = {*fReaderPe, "wS1CDF50"};
    wS1CDF75 = {*fReaderPe, "wS1CDF75"};
    wS1CDF90 = {*fReaderPe, "wS1CDF90"};
    wS1CDF95 = {*fReaderPe, "wS1CDF95"};
    wS2CDF = {*fReaderPe, "wS2CDF"};
    wS2CDF5 = {*fReaderPe, "wS2CDF5"};
    wS2CDF10 = {*fReaderPe, "wS2CDF10"};
    wS2CDF25 = {*fReaderPe, "wS2CDF25"};
    wS2CDF50 = {*fReaderPe, "wS2CDF50"};
    wS2CDF75 = {*fReaderPe, "wS2CDF75"};
    wS2CDF90 = {*fReaderPe, "wS2CDF90"};
    wS2CDF95 = {*fReaderPe, "wS2CDF95"};
    xS1T = {*fReaderPe, "xS1T"};
    yS1T = {*fReaderPe, "yS1T"};
    xS1B = {*fReaderPe, "xS1B"};
    yS1B = {*fReaderPe, "yS1B"};
    xS2T = {*fReaderPe, "xS2T"};
    yS2T = {*fReaderPe, "yS2T"};
    xS2B = {*fReaderPe, "xS2B"};
    yS2B = {*fReaderPe, "yS2B"};
    xS1T_cor = {*fReaderPe, "xS1T_cor"};
    yS1T_cor = {*fReaderPe, "yS1T_cor"};
    xS1B_cor = {*fReaderPe, "xS1B_cor"};
    yS1B_cor = {*fReaderPe, "yS1B_cor"};
    xS2T_cor = {*fReaderPe, "xS2T_cor"};
    yS2T_cor = {*fReaderPe, "yS2T_cor"};
    xS2B_cor = {*fReaderPe, "xS2B_cor"};
    yS2B_cor = {*fReaderPe, "yS2B_cor"};
    xS2_cdfTMs = {*fReaderPe, "xS2_cdfTMs"};
    yS2_cdfTMs = {*fReaderPe, "yS2_cdfTMs"};
    nHitS1 = {*fReaderPe, "nHitS1"};
    nPMTS1 = {*fReaderPe, "nPMTS1"};
    nPMTS1T = {*fReaderPe, "nPMTS1T"};
    nPMTS1B = {*fReaderPe, "nPMTS1B"};
    nSatS1 = {*fReaderPe, "nSatS1"};
    nHitS2 = {*fReaderPe, "nHitS2"};
    nPMTS2 = {*fReaderPe, "nPMTS2"};
    nPMTS2T = {*fReaderPe, "nPMTS2T"};
    nPMTS2B = {*fReaderPe, "nPMTS2B"};
    nSatS2 = {*fReaderPe, "nSatS2"};
    nPeakS1 = {*fReaderPe, "nPeakS1"};
    nPeakS2 = {*fReaderPe, "nPeakS2"};
    nSignals = {*fReaderPe, "nSignals"};
    qTotal = {*fReaderPe, "qTotal"};
    qElse = {*fReaderPe, "qElse"};
    qSignals_total_before_S2max = {*fReaderPe, "qSignals_total_before_S2max"};
    qElse_max_before_S2max = {*fReaderPe, "qElse_max_before_S2max"};
    qVeto = {*fReaderPe, "qVeto"};
    qNearS1max = {*fReaderPe, "qNearS1max"};
    qNearS2max = {*fReaderPe, "qNearS2max"};
    qElseBeforeS1max = {*fReaderPe, "qElseBeforeS1max"};
    qElseBetweenS1S2max = {*fReaderPe, "qElseBetweenS1S2max"};
    qElseAfterS2max = {*fReaderPe, "qElseAfterS2max"};
    qElseMaxChannelNumber = {*fReaderPe, "qElseMaxChannelNumber"};
    qElseMaxChannel = {*fReaderPe, "qElseMaxChannel"};
    nSignalBeforeS1max = {*fReaderPe, "nSignalBeforeS1max"};
    nSignalBetweenS1S2max = {*fReaderPe, "nSignalBetweenS1S2max"};
    nSignalAfterS2max = {*fReaderPe, "nSignalAfterS2max"};
    ratioTSignal = {*fReaderPe, "ratioTSignal"};
    nSinglePhoton = {*fReaderPe, "nSinglePhoton"};
    nSingleElectron = {*fReaderPe, "nSingleElectron"};
    nS1Total = {*fReaderPe, "nS1Total"};
    nS2Total = {*fReaderPe, "nS2Total"};
    nS1PreS2max = {*fReaderPe, "nS1PreS2max"};
    nS2PreS2max = {*fReaderPe, "nS2PreS2max"};
    duration = {*fReaderPe, "duration"};
    qTotalPreEvent = {*fReaderPe, "qTotalPreEvent"};
    qS2maxPreEvent = {*fReaderPe, "qS2maxPreEvent"};
    tDurationPreEvent = {*fReaderPe, "tDurationPreEvent"};
    tDiffPreEvent = {*fReaderPe, "tDiffPreEvent"};
    qLargeEvent = {*fReaderPe, "qLargeEvent"};
    tLargeEvent = {*fReaderPe, "tLargeEvent"};
    qLargeSignal = {*fReaderPe, "qLargeSignal"};
    tLargeSignal = {*fReaderPe, "tLargeSignal"};
    deadtime = {*fReaderPe, "deadtime"};
    ratioqS1PrePeak = {*fReaderPe, "ratioqS1PrePeak"};
    ratioqS2PrePeak = {*fReaderPe, "ratioqS2PrePeak"};
    ratioqS1PrePeakSmr = {*fReaderPe, "ratioqS1PrePeakSmr"};
    ratioqS2PrePeakSmr = {*fReaderPe, "ratioqS2PrePeakSmr"};
    qS1TmaxHitCharge = {*fReaderPe, "qS1TmaxHitCharge"};
    qS1BmaxHitCharge = {*fReaderPe, "qS1BmaxHitCharge"};
    qS2TmaxHitCharge = {*fReaderPe, "qS2TmaxHitCharge"};
    qS2BmaxHitCharge = {*fReaderPe, "qS2BmaxHitCharge"};
    qS1maxHitCharge = {*fReaderPe, "qS1maxHitCharge"};
    qS1maxChannelCharge = {*fReaderPe, "qS1maxChannelCharge"};
    qS2maxHitCharge = {*fReaderPe, "qS2maxHitCharge"};
    qS2maxChannelCharge = {*fReaderPe, "qS2maxChannelCharge"};
    qS1hitStdev = {*fReaderPe, "qS1hitStdev"};
    qS1hitStdevTo1 = {*fReaderPe, "qS1hitStdevTo1"};
    qS1channelStdev = {*fReaderPe, "qS1channelStdev"};
    qS1channelStdevTo1 = {*fReaderPe, "qS1channelStdevTo1"};
    qS2hitStdev = {*fReaderPe, "qS2hitStdev"};
    qS2hitStdevTo1 = {*fReaderPe, "qS2hitStdevTo1"};
    qS2channelStdev = {*fReaderPe, "qS2channelStdev"};
    qS2channelStdevTo1 = {*fReaderPe, "qS2channelStdevTo1"};
    rmsCogS1T = {*fReaderPe, "rmsCogS1T"};
    rmsCogS1B = {*fReaderPe, "rmsCogS1B"};
    rmsMaxQPMTPosS2T = {*fReaderPe, "rmsMaxQPMTPosS2T"};
    tbaMaxS2F = {*fReaderPe, "tbaMaxS2F"};
    xMaxS2F = {*fReaderPe, "xMaxS2F"};
    yMaxS2F = {*fReaderPe, "yMaxS2F"}; 
    hitStdevMaxS2F = {*fReaderPe, "hitStdevMaxS2F"};
    topRmsMaxS2F = {*fReaderPe, "topRmsMaxS2F"};
    qChMaxS2F = {*fReaderPe, "qChMaxS2F"};
    qMaxS2F = {*fReaderPe, "qMaxS2F"};
    wMaxS2F = {*fReaderPe, "wMaxS2F"};
    xS2max_TM = {*fReaderPe, "xS2max_TM"};
    yS2max_TM = {*fReaderPe, "yS2max_TM"};
    lS2max_TM = {*fReaderPe, "lS2max_TM"};
    xS2max_TMs = {*fReaderPe, "xS2max_TMs"};
    yS2max_TMs = {*fReaderPe, "yS2max_TMs"};
    rms_TM = {*fReaderPe, "rms_TM"};
    xS2max_PAF = {*fReaderPe, "xS2max_PAF"};
    yS2max_PAF = {*fReaderPe, "yS2max_PAF"};
    lhfS2max_PAF = {*fReaderPe, "lhfS2max_PAF"};
    xS2max_cdfTM = {*fReaderPe, "xS2max_cdfTM"};
    yS2max_cdfTM = {*fReaderPe, "yS2max_cdfTM"};
    lS2max_cdfTM = {*fReaderPe, "lS2max_cdfTM"};
    xS2max_cdfTMs = {*fReaderPe, "xS2max_cdfTMs"};
    yS2max_cdfTMs = {*fReaderPe, "yS2max_cdfTMs"};
    rms_cdfTM = {*fReaderPe, "rms_cdfTM"};
    xS2max_cdfPAF = {*fReaderPe, "xS2max_cdfPAF"};
    yS2max_cdfPAF = {*fReaderPe, "yS2max_cdfPAF"};
    lhfS2max_cdfPAF = {*fReaderPe, "lhfS2max_cdfPAF"};
    //	S1Density = {*fReaderPe, "S1Density"};
    //	GateCharge = {*fReaderPe, "GateCharge"};
    //	tNoise = {*fReaderPe, "tNoise"};

    // merge info
    nSubSignals_S2max = {*fReaderPe, "nSubSignals_S2max"};
    nSubSignals5_S2max = {*fReaderPe, "nSubSignals5_S2max"};
    average_deltaT_signal_S2max = {*fReaderPe, "average_deltaT_signal_S2max"};
    ratioSubSignals_S2max = {*fReaderPe, "ratioSubSignals_S2max"};
    chargeSubSignals_S2max = {*fReaderPe, "chargeSubSignals_S2max"};
}

void EventSelector::CreateBranches() {

    os_tree = new TTree("out_tree", "ana Tree");
    os_tree->Branch("runNumber", &o_runNumber, "runNumber/I");
    os_tree->Branch("fileNumber", &o_fileNumber, "fileNumber/I");
    os_tree->Branch("eventNumber", &o_eventNumber, "eventNumber/I");
    os_tree->Branch("t", &o_t, "t/l");
    os_tree->Branch("iS1_max", &o_iS1_max, "iS1_max/I");
    os_tree->Branch("iS1_max_charge_pairing", &o_iS1_max_charge_pairing, "iS1_max_charge_pairing/I");
    os_tree->Branch("iRealS1_max_charge_pairing", &o_iRealS1_max_charge_pairing, "iRealS1_max_charge_pairing/I");
    os_tree->Branch("iS2_max", &o_iS2_max, "iS2_max/I");
    os_tree->Branch("tS1_max", &o_tS1_max, "tS1_max/l");
    os_tree->Branch("tS1_max_charge_pairing", &o_tS1_max_charge_pairing, "tS1_max_charge_pairing/l");
    os_tree->Branch("tS2_max", &o_tS2_max, "tS2_max/l");
    os_tree->Branch("hS1_max", &o_hS1_max, "hS1_max/F");
    os_tree->Branch("hS1_max_charge_pairing", &o_hS1_max_charge_pairing, "hS1_max_charge_pairing/F");
    os_tree->Branch("hS2_max", &o_hS2_max, "hS2_max/F");
    os_tree->Branch("wS1_max", &o_wS1_max, "wS1_max/F");
    os_tree->Branch("wS1_max_charge_pairing", &o_wS1_max_charge_pairing, "wS1_max_charge_pairing/F");
    os_tree->Branch("wS2_max", &o_wS2_max, "wS2_max/F");
    os_tree->Branch("wS1CDF_max", &o_wS1CDF_max, "wS1CDF_max/F");
    os_tree->Branch("wS2CDF_max", &o_wS2CDF_max, "wS2CDF_max/F");
    os_tree->Branch("wS2FWHM_max", &o_wS2FWHM_max, "wS2FWHM_max/F");
    os_tree->Branch("widthTenS2_max", &o_widthTenS2_max, "widthTenS2_max/F");
    os_tree->Branch("xS1T_max", &o_xS1T_max, "xS1T_max/F");
    os_tree->Branch("yS1T_max", &o_yS1T_max, "yS1T_max/F");
    os_tree->Branch("xS2T_max", &o_xS2T_max, "xS2T_max/F");
    os_tree->Branch("yS2T_max", &o_yS2T_max, "yS2T_max/F");
    os_tree->Branch("xS1Tcor_max", &o_xS1Tcor_max, "xS1Tcor_max/F");
    os_tree->Branch("yS1Tcor_max", &o_yS1Tcor_max, "yS1Tcor_max/F");
    os_tree->Branch("xS2Tcor_max", &o_xS2Tcor_max, "xS2Tcor_max/F");
    os_tree->Branch("yS2Tcor_max", &o_yS2Tcor_max, "yS2Tcor_max/F");
    os_tree->Branch("xS1B_max", &o_xS1B_max, "xS1B_max/F");
    os_tree->Branch("yS1B_max", &o_yS1B_max, "yS1B_max/F");
    os_tree->Branch("xS2B_max", &o_xS2B_max, "xS2B_max/F");
    os_tree->Branch("yS2B_max", &o_yS2B_max, "yS2B_max/F");
    os_tree->Branch("xS1Bcor_max", &o_xS1Bcor_max, "xS1Bcor_max/F");
    os_tree->Branch("yS1Bcor_max", &o_yS1Bcor_max, "yS1Bcor_max/F");
    os_tree->Branch("xS2Bcor_max", &o_xS2Bcor_max, "xS2Bcor_max/F");
    os_tree->Branch("yS2Bcor_max", &o_yS2Bcor_max, "yS2Bcor_max/F");
    os_tree->Branch("xS2max_TM", &o_xS2max_TM, "xS2max_TM/F");
    os_tree->Branch("yS2max_TM", &o_yS2max_TM, "yS2max_TM/F");
    os_tree->Branch("xS2max_TMs", &o_xS2max_TMs, "xS2max_TMs/F");
    os_tree->Branch("yS2max_TMs", &o_yS2max_TMs, "yS2max_TMs/F");
    os_tree->Branch("lS2max_TM", &o_lS2max_TM, "lS2max_TM/F");
    os_tree->Branch("rms_TM", &o_rms_TM, "rms_TM/F");
    os_tree->Branch("xS2max_PAF", &o_xS2max_PAF, "xS2max_PAF/F");
    os_tree->Branch("yS2max_PAF", &o_yS2max_PAF, "yS2max_PAF/F");
    os_tree->Branch("lhfS2max_PAF", &o_lhfS2max_PAF, "lhfS2max_PAF/F");
    os_tree->Branch("xS2max_cdfTM", &o_xS2max_cdfTM, "xS2max_cdfTM/F");
    os_tree->Branch("yS2max_cdfTM", &o_yS2max_cdfTM, "yS2max_cdfTM/F");
    os_tree->Branch("xS2max_cdfTMs", &o_xS2max_cdfTMs, "xS2max_cdfTMs/F");
    os_tree->Branch("yS2max_cdfTMs", &o_yS2max_cdfTMs, "yS2max_cdfTMs/F");
    os_tree->Branch("lS2max_cdfTM", &o_lS2max_cdfTM, "lS2max_cdfTM/F");
    os_tree->Branch("rms_cdfTM", &o_rms_cdfTM, "rms_cdfTM/F");
    os_tree->Branch("xS2max_cdfTMs_cor", &o_xS2max_cdfTMs_cor,
                    "xS2max_cdfTMs_cor/F");
    os_tree->Branch("yS2max_cdfTMs_cor", &o_yS2max_cdfTMs_cor,
                    "yS2max_cdfTMs_cor/F");
    os_tree->Branch("xS2max_cdfPAF", &o_xS2max_cdfPAF, "xS2max_cdfPAF/F");
    os_tree->Branch("yS2max_cdfPAF", &o_yS2max_cdfPAF, "yS2max_cdfPAF/F");
    os_tree->Branch("lhfS2max_cdfPAF", &o_lhfS2max_cdfPAF, "lhfS2max_cdfPAF/F");

    os_tree->Branch("qS1C_max", &o_qS1C_max, "qS1C_max/F");
    os_tree->Branch("qS1TC_max", &o_qS1TC_max, "qS1TC_max/F");
    os_tree->Branch("qS1BC_max", &o_qS1BC_max, "qS1BC_max/F");
    os_tree->Branch("qS1_max2", &o_qS1_max2, "qS1_max2/F");
    os_tree->Branch("qS1T_max2", &o_qS1T_max2, "qS1T_max2/F");
    os_tree->Branch("qS1B_max2", &o_qS1B_max2, "qS1B_max2/F");
    os_tree->Branch("qS1C_max2", &o_qS1C_max2, "qS1C_max2/F");
    os_tree->Branch("qS1TC_max2", &o_qS1TC_max2, "qS1TC_max2/F");
    os_tree->Branch("qS1BC_max2", &o_qS1BC_max2, "qS1BC_max2/F");
    os_tree->Branch("qS2C_max", &o_qS2C_max, "qS2C_max/F");
    os_tree->Branch("qS2BC_max", &o_qS2BC_max, "qS2BC_max/F");
    os_tree->Branch("qS1_C", &o_qS1_C, "qS1_C/F");
    os_tree->Branch("qS1T_C", &o_qS1T_C, "qS1T_C/F");
    os_tree->Branch("qS1B_C", &o_qS1B_C, "qS1B_C/F");
    os_tree->Branch("qS1_C2", &o_qS1_C2, "qS1_C2/F");
    os_tree->Branch("qS1T_C2", &o_qS1T_C2, "qS1T_C2/F");
    os_tree->Branch("qS1B_C2", &o_qS1B_C2, "qS1B_C2/F");
    os_tree->Branch("qS2_C", &o_qS2_C, "qS2_C/F");
    os_tree->Branch("qS2B_C", &o_qS2B_C, "qS2B_C/F");
    os_tree->Branch("factor1", &o_factor1, "factor1/F");
    os_tree->Branch("factor2", &o_factor2, "factor2/F");
    os_tree->Branch("qS1C_maxs", &o_qS1C_maxs, "qS1C_maxs/F");
    os_tree->Branch("qS2BC_maxs", &o_qS2BC_maxs, "qS2BC_maxs/F");
    os_tree->Branch("qS1_Cs", &o_qS1_Cs, "qS1_Cs/F");
    os_tree->Branch("qS2B_Cs", &o_qS2B_Cs, "qS2B_Cs/F");

    os_tree->Branch("qS1_max", &o_qS1_max, "qS1_max/F");
    os_tree->Branch("qS1_max_charge_pairing", &o_qS1_max_charge_pairing, "qS1_max_charge_pairing/F");
    os_tree->Branch("qS1T_max", &o_qS1T_max, "qS1T_max/F");
    os_tree->Branch("qS1B_max", &o_qS1B_max, "qS1B_max/F");
    os_tree->Branch("qS2_max", &o_qS2_max, "qS2_max/F");
    os_tree->Branch("qS2B_max", &o_qS2B_max, "qS2B_max/F");
    os_tree->Branch("qS2T_max", &o_qS2T_max, "qS2T_max/F");
    os_tree->Branch("qS1Veto_max", &o_qS1Veto_max, "qS1Veto_max/F");
    os_tree->Branch("qS1VetoT_max", &o_qS1VetoT_max, "qS1VetoT_max/F");
    os_tree->Branch("qS1VetoB_max", &o_qS1VetoB_max, "qS1VetoB_max/F");

    os_tree->Branch("dt", &o_dt, "dt/F");
    os_tree->Branch("nPMTS1_max", &o_nPMTS1_max, "nPMTS1_max/F");
    os_tree->Branch("nPMTS2_max", &o_nPMTS2_max, "nPMTS2_max/F");
    os_tree->Branch("qSparking", &o_qSparking, "qSparking/F");
    os_tree->Branch("qPMTSparking", &o_qPMTSparking, "qPMTSparking/F");
    os_tree->Branch("qUnknown", &o_qUnknown, "qUnknown/F");
    os_tree->Branch("qOthers", &o_qOthers, "qOthers/F");
    os_tree->Branch("nSignals", &o_nSignals, "nSignals/I");
    os_tree->Branch("qTotal", &o_qTotal, "qTotal/F");
    os_tree->Branch("qElse", &o_qElse, "qElse/F");
    os_tree->Branch("qVeto", &o_qVeto, "qVeto/F");
    os_tree->Branch("qNearS1max", &o_qNearS1max, "qNearS1max/F");
    os_tree->Branch("qNearS2max", &o_qNearS2max, "qNearS2max/F");
    os_tree->Branch("qSignals_total_before_S2max", &o_qSignals_total_before_S2max, "qSignals_total_before_S2max/F");
    os_tree->Branch("qElse_max_before_S2max", &o_qElse_max_before_S2max,
                    "qElse_max_before_S2max/F");
    os_tree->Branch("qElseBeforeS1max", &o_qElseBeforeS1max,
                    "qElseBeforeS1max/F");
    os_tree->Branch("qElseBetweenS1S2max", &o_qElseBetweenS1S2max,
                    "qElseBetweenS1S2max/F");
    os_tree->Branch("qElseAfterS2max", &o_qElseAfterS2max, "qElseAfterS2max/F");
    os_tree->Branch("qElseMaxChannelNumber", &o_qElseMaxChannelNumber,
                    "qElseMaxChannelNumber/I");
    os_tree->Branch("qElseMaxChannel", &o_qElseMaxChannel, "qElseMaxChannel/F");
    os_tree->Branch("nSignalBeforeS1max", &o_nSignalBeforeS1max,
                    "nSignalBeforeS1max/I");
    os_tree->Branch("nSignalBetweenS1S2max", &o_nSignalBetweenS1S2max,
                    "nSignalBetweenS1S2max/I");
    os_tree->Branch("nSignalAfterS2max", &o_nSignalAfterS2max,
                    "nSignalAfterS2max/I");

    os_tree->Branch("ratioTSignal", &o_ratioTSignal, "ratioTSignal/F");
    os_tree->Branch("qLargeSignal", &o_qLargeSignal, "qLargeSignal/F");
    os_tree->Branch("tLargeSignal", &o_tLargeSignal, "tLargeSignal/l");
    os_tree->Branch("qLargeEvent", &o_qLargeEvent, "qLargeEvent/F");
    os_tree->Branch("tLargeEvent", &o_tLargeEvent, "tLargeEvent/l");

    os_tree->Branch("deadtime", &o_deadtime, "deadtime/O");
    if(deadtime_scale_factor == -1){
        os_tree->Branch("nScaleFactor", &o_nScaleFactor, "nScaleFactor/I");
        os_tree->Branch("deadtime_adaptive", &o_deadtime_adaptive, "deadtime_adaptive[nScaleFactor]/O");
    } else {
        os_tree->Branch("deadtime_adaptive", &o_deadtime_adaptive_i, "deadtime_adaptive/O");
    }

    os_tree->Branch("duration", &o_duration, "duration/l");
    os_tree->Branch("qTotalPreEvent", &o_qTotalPreEvent, "qTotalPreEvent/F");
    os_tree->Branch("qS2maxPreEvent", &o_qS2maxPreEvent, "qS2maxPreEvent/F");
    os_tree->Branch("tDiffPreEvent", &o_tDiffPreEvent, "tDiffPreEvent/l");

    os_tree->Branch("nS1", &o_nS1, "nS1/I");
    os_tree->Branch("nPostS1", &o_nPostS1, "nPostS1/I");
    os_tree->Branch("nGoodS1", &o_nGoodS1, "nGoodS1/I");
    os_tree->Branch("nCandidateS1", &o_nCandidateS1, "nCandidateS1/I");
    os_tree->Branch("nS2", &o_nS2, "nS2/I");
    os_tree->Branch("nPostS2", &o_nPostS2, "nPostS2/I");
    os_tree->Branch("nRealPostS2", &o_nRealPostS2, "nRealPostS2/I");
    os_tree->Branch("nPMTSparking", &o_nPMTSparking, "nPMTSparking/I");
    os_tree->Branch("nSparking", &o_nSparking, "nSparking/I");
    os_tree->Branch("nNoise", &o_nNoise, "nNoise/I");
    os_tree->Branch("nUnknown", &o_nUnknown, "nUnknown/I");
    os_tree->Branch("nOthers", &o_nOthers, "nOthers/I");
    os_tree->Branch("nPeakS1_max", &o_nPeakS1_max, "nPeakS1_max/F");
    os_tree->Branch("nPeakS2_max", &o_nPeakS2_max, "nPeakS2_max/F");
    os_tree->Branch("ratioqS2PrePeak_max", &o_ratioqS2PrePeak_max,
                    "ratioqS2PrePeak_max/F");
    os_tree->Branch("ratioqS2PrePeakSmr_max", &o_ratioqS2PrePeakSmr_max,
                    "ratioqS2PrePeakSmr_max/F");
    os_tree->Branch("ratioqS1PrePeak_max", &o_ratioqS1PrePeak_max,
                    "ratioqS1PrePeak_max/F");
    os_tree->Branch("ratioqS1PrePeakSmr_max", &o_ratioqS1PrePeakSmr_max,
                    "ratioqS1PrePeakSmr_max/F");
    os_tree->Branch("qS1TmaxHitCharge_max", &o_qS1TmaxHitCharge_max,
                    "qS1TmaxHitCharge_max/F");
    os_tree->Branch("qS1BmaxHitCharge_max", &o_qS1BmaxHitCharge_max,
                    "qS1BmaxHitCharge_max/F");
    os_tree->Branch("qS2TmaxHitCharge_max", &o_qS2TmaxHitCharge_max,
                    "qS2TmaxHitCharge_max/F");
    os_tree->Branch("qS2BmaxHitCharge_max", &o_qS2BmaxHitCharge_max,
                    "qS2BmaxHitCharge_max/F");

    os_tree->Branch("qS1maxHitCharge_max", &o_qS1maxHitCharge_max,
                    "qS1maxHitCharge_max/F");
    os_tree->Branch("qS1maxChannelCharge_max", &o_qS1maxChannelCharge_max,
                    "qS1maxChannelCharge_max/F");
    os_tree->Branch("qS2maxHitCharge_max", &o_qS2maxHitCharge_max,
                    "qS2maxHitCharge_max/F");
    os_tree->Branch("qS2maxChannelCharge_max", &o_qS2maxChannelCharge_max,
                    "qS2maxChannelCharge_max/F");

    os_tree->Branch("qS1hitStdev_max", &o_qS1hitStdev_max, "qS1hitStdev_max/F");
    os_tree->Branch("qS1channelStdev_max", &o_qS1channelStdev_max,
                    "qS1channelStdev_max/F");
    os_tree->Branch("qS2hitStdev_max", &o_qS2hitStdev_max, "qS2hitStdev_max/F");
    os_tree->Branch("qS2channelStdev_max", &o_qS2channelStdev_max,
                    "qS2channelStdev_max/F");

    os_tree->Branch("qS1hitStdevTo1_max", &o_qS1hitStdevTo1_max,
                    "qS1hitStdevTo1_max/F");
    os_tree->Branch("qS1channelStdevTo1_max", &o_qS1channelStdevTo1_max,
                    "qS1channelStdevTo1_max/F");
    os_tree->Branch("qS2hitStdevTo1_max", &o_qS2hitStdevTo1_max,
                    "qS2hitStdevTo1_max/F");
    os_tree->Branch("qS2channelStdevTo1_max", &o_qS2channelStdevTo1_max,
                    "qS2channelStdevTo1_max/F");

    os_tree->Branch("rmsCogS1T_max", &o_rmsCogS1T_max, "rmsCogS1T_max/F");
    os_tree->Branch("rmsCogS1B_max", &o_rmsCogS1B_max, "rmsCogS1B_max/F");
  
    os_tree->Branch("wS1CDF5_max", &o_wS1CDF5_max, "wS1CDF5_max/I");
    os_tree->Branch("wS1CDF10_max", &o_wS1CDF10_max, "wS1CDF10_max/I");
    os_tree->Branch("wS1CDF25_max", &o_wS1CDF25_max, "wS1CDF25_max/I");
    os_tree->Branch("wS1CDF50_max", &o_wS1CDF50_max, "wS1CDF50_max/I");
    os_tree->Branch("wS1CDF75_max", &o_wS1CDF75_max, "wS1CDF75_max/I");
    os_tree->Branch("wS1CDF90_max", &o_wS1CDF90_max, "wS1CDF90_max/I");
    os_tree->Branch("wS1CDF95_max", &o_wS1CDF95_max, "wS1CDF95_max/I");
    os_tree->Branch("wS2CDF5_max", &o_wS2CDF5_max, "wS2CDF5_max/I");
    os_tree->Branch("wS2CDF10_max", &o_wS2CDF10_max, "wS2CDF10_max/I");
    os_tree->Branch("wS2CDF25_max", &o_wS2CDF25_max, "wS2CDF25_max/I");
    os_tree->Branch("wS2CDF50_max", &o_wS2CDF50_max, "wS2CDF50_max/I");
    os_tree->Branch("wS2CDF75_max", &o_wS2CDF75_max, "wS2CDF75_max/I");
    os_tree->Branch("wS2CDF90_max", &o_wS2CDF90_max, "wS2CDF90_max/I");
    os_tree->Branch("wS2CDF95_max", &o_wS2CDF95_max, "wS2CDF95_max/I");
    os_tree->Branch("nHitS1_max", &o_nHitS1_max, "nHitS1_max/I");
    os_tree->Branch("nPMTS1T_max", &o_nPMTS1T_max, "nPMTS1T_max/I");
    os_tree->Branch("nPMTS1B_max", &o_nPMTS1B_max, "nPMTS1B_max/I");
    os_tree->Branch("nHitS2_max", &o_nHitS2_max, "nHitS2_max/I");
    os_tree->Branch("nPMTS2T_max", &o_nPMTS2T_max, "nPMTS2T_max/I");
    os_tree->Branch("nPMTS2B_max", &o_nPMTS2B_max, "nPMTS2B_max/I");

    os_tree->Branch("rmsMaxQPMTPosS2T_max", &o_rmsMaxQPMTPosS2T_max, "rmsMaxQPMTPosS2T_max/F");
    os_tree->Branch("tbaMaxS2F", &o_tbaMaxS2F, "tbaMaxS2F/F");
    os_tree->Branch("hitStdevMaxS2F", &o_hitStdevMaxS2F, "hitStdevMaxS2F/F");
    os_tree->Branch("topRmsMaxS2F", &o_topRmsMaxS2F, "topRmsMaxS2F/F");
    os_tree->Branch("xMaxS2F", &o_xMaxS2F, "xMaxS2F/F");
    os_tree->Branch("yMaxS2F", &o_yMaxS2F, "yMaxS2F/F"); 
    os_tree->Branch("qChMaxS2F", &o_qChMaxS2F, "qChMaxS2F/F");
    os_tree->Branch("qMaxS2F", &o_qMaxS2F, "qMaxS2F/F");
    os_tree->Branch("wMaxS2F", &o_wMaxS2F, "wMaxS2F/I");

    os_tree->Branch("basicCut", &o_basicCut, "basicCut/O");
    os_tree->Branch("deadtime_enhanceCut", &o_deadtime_enhanceCut,
                    "deadtime_enhanceCut/O");
    os_tree->Branch("fv_extendCut", &o_fv_extendCut, "fv_extendCut/O");
    os_tree->Branch("S1PerPmtCut", &o_S1PerPmtCut, "S1PerPmtCut/O");
    os_tree->Branch("S1PatternCut", &o_S1PatternCut, "S1PatternCut/O");
    os_tree->Branch("S1AsyCut", &o_S1AsyCut, "S1AsyCut/O");
    os_tree->Branch("S2ShapeCut", &o_S2ShapeCut, "S2ShapeCut/O");
    os_tree->Branch("gas_s2Cut", &o_gas_s2Cut, "gas_s2Cut/O");
    os_tree->Branch("S2AsyCut", &o_S2AsyCut, "S2AsyCut/O");
    os_tree->Branch("S2TBACut", &o_S2TBACut, "S2TBACut/O");
    os_tree->Branch("drCut", &o_drCut, "drCut/O");
    os_tree->Branch("wallCut", &o_wallCut, "wallCut/O");
    os_tree->Branch("diffusion_enhanceCut", &o_diffusion_enhanceCut,
                    "diffusion_enhanceCut/O");
    os_tree->Branch("ssCut", &o_ssCut, "ssCut/O");

    // merge info
    os_tree->Branch("nSubSignals_S2max", &o_nSubSignals_S2max, "nSubSignals_S2max/I");
    os_tree->Branch("nSubSignals5_S2max", &o_nSubSignals5_S2max, "nSubSignals5_S2max/I");
    os_tree->Branch("average_deltaT_signal_S2max", &o_average_deltaT_signal_S2max, "average_deltaT_signal_S2max/F");
    os_tree->Branch("ratioSubSignals_S2max", &o_ratioSubSignals_S2max, "ratioSubSignals_S2max/F");
    os_tree->Branch("chargeSubSignals_S2max", &o_chargeSubSignals_S2max, "chargeSubSignals_S2max/F");
}

void EventSelector::CreateArrayBranches() {
    os_tree->Branch("qS2", &o_qS2, "qS2[nS2]/F");
    os_tree->Branch("qS2T", &o_qS2T, "qS2T[nS2]/F");
    os_tree->Branch("qS2B", &o_qS2B, "qS2B[nS2]/F");
    os_tree->Branch("xS2T_cor", &o_xS2T_cor, "xS2T_cor[nS2]/F");
    os_tree->Branch("yS2T_cor", &o_yS2T_cor, "yS2T_cor[nS2]/F");
    os_tree->Branch("tS2", &o_tS2, "tS2[nS2]/l");
    os_tree->Branch("qS2C", &o_qS2C, "qS2C[nS2]/F");
    os_tree->Branch("qS2BC", &o_qS2BC, "qS2BC[nS2]/F");
    os_tree->Branch("wS2", &o_wS2, "wS2[nS2]/I");
    os_tree->Branch("widthTenS2", &o_widthTenS2, "widthTenS2[nS2]/I");
    os_tree->Branch("wS2FWHM", &o_wS2FWHM, "wS2FWHM[nS2]/I");
    os_tree->Branch("wS2CDF", &o_wS2CDF, "wS2CDF[nS2]/I");
    os_tree->Branch("hS2", &o_hS2, "hS2[nS2]/F");
    os_tree->Branch("nPeakS2", &o_nPeakS2, "nPeakS2[nS2]/I");
    os_tree->Branch("nPMTS2", &o_nPMTS2, "nPMTS2[nS2]/I");
    os_tree->Branch("nSatS2", &o_nSatS2, "nSatS2[nS2]/I");
    os_tree->Branch("qS2TmaxHitCharge", &o_qS2TmaxHitCharge,
                    "qS2TmaxHitCharge[nS2]/F");
    os_tree->Branch("qS2BmaxHitCharge", &o_qS2BmaxHitCharge,
                    "qS2BmaxHitCharge[nS2]/F");
    os_tree->Branch("ratioqS2PrePeakSmr", &o_ratioqS2PrePeakSmr,
                    "ratioqS2PrePeakSmr[nS2]/F");
    os_tree->Branch("ratioqS2PrePeak", &o_ratioqS2PrePeak,
                    "ratioqS2PrePeak[nS2]/F");
    os_tree->Branch("iGoodS2", &o_iGoodS2, "iGoodS2[nRealPostS2]/I");
}

void EventSelector::CreateBDTBranch() {
    os_tree->Branch("bdt", &o_bdt, "bdt/F");
}

void EventSelector::CreateBDTReader() {
    reader = new TMVA::Reader("!Color:!Silent");
    reader->AddVariable("qS1", &o_qS1_max);
    reader->AddVariable("qS1C", &o_qS1C_max);
    reader->AddVariable("wS1", &o_wS1_max);
    reader->AddVariable("hS1", &o_hS1_max);
    reader->AddVariable("qS2", &o_qS2_max);
    reader->AddVariable("qS2C", &o_qS2C_max);
    reader->AddVariable("wS2", &o_wS2_max);
    reader->AddVariable("hS2", &o_hS2_max);
    reader->AddVariable("widthTenS2", &o_widthTenS2_max);
    reader->AddVariable("S1Asy", &o_S1Asy);
    reader->AddVariable("S2Asy", &o_S2Asy);
    reader->AddVariable("nPeakS1", &o_nPeakS1_max);
    reader->AddVariable("qS1BmaxHitCharge", &o_qS1BmaxHitCharge_max);
    reader->BookMVA("BDT Method", xml_file_name.Data());
}

void EventSelector::EvaluateBDT() { o_bdt = reader->EvaluateMVA("BDT Method"); }

void EventSelector::SetPeOutputTreeValue() {
    o_runNumber = *runNumber;
    o_fileNumber = *fileNumber;
    o_eventNumber = *eventNumber;
    o_tS1_max_charge_pairing = *tS1_max_charge_pairing;
    o_tS1_max = *tS1_max;
    o_tS2_max = *tS2_max;
    o_t = *t;
    o_iS1_max = *iS1_max;
    o_iS1_max_charge_pairing = *iS1_max_charge_pairing;
    o_iRealS1_max_charge_pairing = *iRealS1_max_charge_pairing;
    o_iS2_max = *iS2_max;
    o_nCandidateS1 = *nCandidateS1;
    o_nS1 = *nS1;
    o_nPostS1 = 0;
    o_nGoodS1 = 0;
    o_nS2 = *nS2;
    o_nPostS2 = 0;
    o_nRealPostS2 = 0;
    o_nPMTSparking = *nPMTSparking;
    o_nSparking = *nSparking;
    o_nNoise = *nNoise;
    o_nUnknown = *nUnknown;
    o_nOthers = *nOthers;
    o_hS1_max = *hS1_max;
    o_hS1_max_charge_pairing = *hS1_max_charge_pairing;
    o_hS2_max = *hS2_max;
    o_wS1_max = *wS1_max;
    o_wS1_max_charge_pairing = *wS1_max_charge_pairing;
    o_wS2_max = *wS2_max;
    o_wS1CDF_max = wS1CDF[*iS1_max];
    o_wS2CDF_max = wS2CDF[*iS2_max];
    o_wS2FWHM_max = wS2FWHM[*iS2_max];
    o_widthTenS2_max = widthTenS2[*iS2_max];
    o_qS1_max = *qS1_max;
    o_qS1_max_charge_pairing = *qS1_max_charge_pairing;
    o_qS1T_max = *qS1T_max;
    o_qS1B_max = *qS1B_max;
    if (o_nS1 - o_iS1_max >= 2) {
        o_qS1_max2 = qS1[*iS1_max + 1];
        o_qS1T_max2 = qS1T[*iS1_max + 1];
        o_qS1B_max2 = qS1B[*iS1_max + 1];
    } else {
        o_qS1_max2 = 0;
        o_qS1T_max2 = 0;
        o_qS1B_max2 = 0;
    }
    o_qS1Veto_max = qS1Veto[*iS1_max];
    o_qS1VetoT_max = qS1VetoT[*iS1_max];
    o_qS1VetoB_max = qS1VetoB[*iS1_max];
    o_qS2_max = *qS2_max;
    o_qS2T_max = *qS2T_max;
    o_qS2B_max = *qS2B_max;

    o_qS1C_max = 0;
    o_qS1TC_max = 0;
    o_qS1BC_max = 0;
    o_qS1C_max2 = 0;
    o_qS1TC_max2 = 0;
    o_qS1BC_max2 = 0;
    o_qS2C_max = 0;
    o_qS2BC_max = 0;
    o_qS1_C = 0;
    o_qS1T_C = 0;
    o_qS1B_C = 0;
    o_qS1_C2 = 0;
    o_qS1T_C2 = 0;
    o_qS1B_C2 = 0;
    o_qS2_C = 0;
    o_qS2B_C = 0;
    o_factor1 = 0;
    o_factor2 = 0;
    o_qS1_Cs = 0;
    o_qS2B_Cs = 0;
    o_qS1C_maxs = 0;
    o_qS2BC_maxs = 0;
    o_S1Asy = (qS1T[*iS1_max] - qS1B[*iS1_max]) / (qS1[*iS1_max]);
    o_S2Asy = (qS2T[*iS2_max] - qS2B[*iS2_max]) / (qS2[*iS2_max]);

    o_dt = 4 * (float(*tS2_max - *tS1_max));
    o_nPMTS1_max = nPMTS1[*iS1_max];
    o_nPMTS2_max = nPMTS2[*iS2_max];
    o_qPMTSparking = *qPMTSparking;
    o_qSparking = *qSparking;
    o_qUnknown = *qUnknown;
    o_qOthers = *qOthers;
    o_nSignals = *nSignals;
    o_qTotal = *qTotal;
    o_qElse = *qElse;
    o_qSignals_total_before_S2max = *qSignals_total_before_S2max;
    o_qElse_max_before_S2max = *qElse_max_before_S2max;
    o_qVeto = *qVeto;
    o_qNearS1max = *qNearS1max;
    o_qNearS2max = *qNearS2max;
    o_qElseBeforeS1max = *qElseBeforeS1max;
    o_qElseBetweenS1S2max = *qElseBetweenS1S2max;
    o_qElseAfterS2max = *qElseAfterS2max;
    o_qElseMaxChannelNumber = *qElseMaxChannelNumber;
    o_qElseMaxChannel = *qElseMaxChannel;
    o_nSignalBeforeS1max = *nSignalBeforeS1max;
    o_nSignalBetweenS1S2max = *nSignalBetweenS1S2max;
    o_nSignalAfterS2max = *nSignalAfterS2max;
    o_ratioTSignal = *ratioTSignal;
    o_tLargeSignal = *tLargeSignal;
    o_qLargeSignal = *qLargeSignal;
    o_tLargeEvent = *tLargeEvent;
    o_qLargeEvent = *qLargeEvent;
    o_qTotalPreEvent = *qTotalPreEvent;
    o_qS2maxPreEvent = *qS2maxPreEvent;

    o_deadtime = *deadtime;
    if (deadtime_scale_factor == -1) {
        o_nScaleFactor = adaptive_deadtime_cut.GetNScaleFactor();
        auto deadtime_adaptive = adaptive_deadtime_cut(*t);
        for (int i = 0; i < o_nScaleFactor;i++) {
            o_deadtime_adaptive[i] = deadtime_adaptive[i];
        }
    } else {
        o_deadtime_adaptive_i = adaptive_deadtime_cut(*t, deadtime_scale_factor);
    }

    o_duration = *duration;
    o_tDiffPreEvent = *tDiffPreEvent;
    o_nPeakS1_max = nPeakS1[*iS1_max];
    o_nPeakS2_max = nPeakS2[*iS2_max];
    o_xS1T_max = *xS1T_max;
    o_yS1T_max = *yS1T_max;
    o_xS2T_max = *xS2T_max;
    o_yS2T_max = *yS2T_max;
    o_xS1Tcor_max = *xS1Tcor_max;
    o_yS1Tcor_max = *yS1Tcor_max;
    o_xS2Tcor_max = *xS2Tcor_max;
    o_yS2Tcor_max = *yS2Tcor_max;
    o_xS1B_max = *xS1B_max;
    o_yS1B_max = *yS1B_max;
    o_xS2B_max = *xS2B_max;
    o_yS2B_max = *yS2B_max;
    o_xS1Bcor_max = *xS1Bcor_max;
    o_yS1Bcor_max = *yS1Bcor_max;
    o_xS2Bcor_max = *xS2Bcor_max;
    o_yS2Bcor_max = *yS2Bcor_max;
    o_xS2max_TM = *xS2max_TM;
    o_yS2max_TM = *yS2max_TM;
    o_xS2max_TMs = *xS2max_TMs;
    o_yS2max_TMs = *yS2max_TMs;
    o_lS2max_TM = *lS2max_TM;
    o_rms_TM = *rms_TM;
    o_xS2max_PAF = *xS2max_PAF;
    o_yS2max_PAF = *yS2max_PAF;
    o_lhfS2max_PAF = *lhfS2max_PAF;
    o_xS2max_cdfTM = *xS2max_cdfTM;
    o_yS2max_cdfTM = *yS2max_cdfTM;
    o_xS2max_cdfTMs = *xS2max_cdfTMs;
    o_yS2max_cdfTMs = *yS2max_cdfTMs;
    o_lS2max_cdfTM = *lS2max_cdfTM;
    o_rms_cdfTM = *rms_cdfTM;
    o_xS2max_cdfPAF = *xS2max_cdfPAF;
    o_yS2max_cdfPAF = *yS2max_cdfPAF;
    o_lhfS2max_cdfPAF = *lhfS2max_cdfPAF;
    o_xS2max_cdfTMs_cor = NAN;
    o_yS2max_cdfTMs_cor = NAN;
    o_ratioqS1PrePeak_max = ratioqS1PrePeak[*iS1_max];
    o_ratioqS1PrePeakSmr_max = ratioqS1PrePeakSmr[*iS1_max];
    o_ratioqS2PrePeak_max = ratioqS2PrePeak[*iS2_max];
    o_ratioqS2PrePeakSmr_max = ratioqS2PrePeakSmr[*iS2_max];
    o_qS1BmaxHitCharge_max = qS1BmaxHitCharge[*iS1_max];
    o_qS1TmaxHitCharge_max = qS1TmaxHitCharge[*iS1_max];
    o_qS2BmaxHitCharge_max = qS2BmaxHitCharge[*iS2_max];
    o_qS2TmaxHitCharge_max = qS2TmaxHitCharge[*iS2_max];

    o_qS1maxHitCharge_max = qS1maxHitCharge[*iS1_max];
    o_qS1maxChannelCharge_max = qS1maxChannelCharge[*iS1_max];
    o_qS2maxHitCharge_max = qS2maxHitCharge[*iS2_max];
    o_qS2maxChannelCharge_max = qS2maxChannelCharge[*iS2_max];

    o_qS1hitStdev_max = qS1hitStdev[*iS1_max];
    o_qS1channelStdev_max = qS1channelStdev[*iS1_max];
    o_qS2hitStdev_max = qS2hitStdev[*iS2_max];
    o_qS2channelStdev_max = qS2channelStdev[*iS2_max];

    o_qS1hitStdevTo1_max = qS1hitStdevTo1[*iS1_max];
    o_qS1channelStdevTo1_max = qS1channelStdevTo1[*iS1_max];
    o_qS2hitStdevTo1_max = qS2hitStdevTo1[*iS2_max];
    o_qS2channelStdevTo1_max = qS2channelStdevTo1[*iS2_max];

    o_rmsCogS1T_max = rmsCogS1T[*iS1_max];
    o_rmsCogS1B_max = rmsCogS1B[*iS1_max];
    o_wS1CDF5_max = wS1CDF5[*iS1_max];
    o_wS1CDF10_max = wS1CDF10[*iS1_max];
    o_wS1CDF25_max = wS1CDF25[*iS1_max];
    o_wS1CDF50_max = wS1CDF50[*iS1_max];
    o_wS1CDF75_max = wS1CDF75[*iS1_max];
    o_wS1CDF90_max = wS1CDF90[*iS1_max];
    o_wS1CDF95_max = wS1CDF95[*iS1_max];
    o_wS2CDF5_max = wS2CDF5[*iS2_max];
    o_wS2CDF10_max = wS2CDF10[*iS2_max];
    o_wS2CDF25_max = wS2CDF25[*iS2_max];
    o_wS2CDF50_max = wS2CDF50[*iS2_max];
    o_wS2CDF75_max = wS2CDF75[*iS2_max];
    o_wS2CDF90_max = wS2CDF90[*iS2_max];
    o_wS2CDF95_max = wS2CDF95[*iS2_max];
    o_nHitS1_max = nHitS1[*iS1_max];
    o_nPMTS1T_max = nPMTS1T[*iS1_max];
    o_nPMTS1B_max = nPMTS1B[*iS1_max];
    o_nHitS2_max = nHitS2[*iS2_max];
    o_nPMTS2T_max = nPMTS2T[*iS2_max];
    o_nPMTS2B_max = nPMTS2B[*iS2_max];
    o_rmsMaxQPMTPosS2T_max = rmsMaxQPMTPosS2T[*iS2_max];
    o_tbaMaxS2F = *tbaMaxS2F;
    o_hitStdevMaxS2F = *hitStdevMaxS2F;
    o_topRmsMaxS2F = *topRmsMaxS2F;
    o_xMaxS2F = *xMaxS2F;
    o_yMaxS2F = *yMaxS2F;
    o_qChMaxS2F = *qChMaxS2F;
    o_qMaxS2F = *qMaxS2F;
    o_wMaxS2F = *wMaxS2F; 

    o_basicCut = true;
    o_deadtime_enhanceCut = true;
    o_S1PerPmtCut = true;
    o_S1PatternCut = true;
    o_S2ShapeCut = true;
    o_gas_s2Cut = true;
    o_drCut = true;
    o_S1AsyCut = true;
    o_S2AsyCut = true;
    o_S2TBACut = true;
    o_wallCut = true;
    o_diffusion_enhanceCut = true;
    o_ssCut = true;
    o_fv_extendCut = true;

    // merge info
    o_nSubSignals_S2max = *nSubSignals_S2max;
    o_nSubSignals5_S2max = *nSubSignals5_S2max;
    o_average_deltaT_signal_S2max = *average_deltaT_signal_S2max;
    o_ratioSubSignals_S2max = *ratioSubSignals_S2max;
    o_chargeSubSignals_S2max = *chargeSubSignals_S2max;
}

void EventSelector::SetPeOutputTreeArray() {
    memset(o_iGoodS2, -1, sizeof(o_iGoodS2));
    for (long long i = 0; i < *nS2; i++) {
        o_qS2[i] = qS2[i];
        o_qS2T[i] = qS2T[i];
        o_qS2B[i] = qS2B[i];
        o_yS2T_cor[i] = yS2T_cor[i];
        o_xS2T_cor[i] = xS2T_cor[i];
	    o_tS2[i] = tS2[i];
        o_qS2C[i] = qS2[i];
        o_qS2BC[i] = qS2B[i];
        o_wS2[i] = wS2[i];
        o_widthTenS2[i] = widthTenS2[i];
        o_wS2FWHM[i] = wS2FWHM[i];
        o_wS2CDF[i] = wS2CDF[i];
        o_hS2[i] = hS2[i];
        o_nPeakS2[i] = nPeakS2[i];
        o_nPMTS2[i] = nPMTS2[i];
        o_nSatS2[i] = nSatS2[i];
        o_qS2TmaxHitCharge[i] = qS2TmaxHitCharge[i];
        o_qS2BmaxHitCharge[i] = qS2BmaxHitCharge[i];
        o_ratioqS2PrePeakSmr[i] = ratioqS2PrePeakSmr[i];
        o_ratioqS2PrePeak[i] = ratioqS2PrePeak[i];
    }
}

void EventSelector::FillPeOutputTree() { os_tree->Fill(); }

void EventSelector::WritePeOutputTree() { os_tree->Write(); }

void EventSelector::CloseOutputFile() { o_file->Close(); }

bool EventSelector::LoadMappingFile() {
    TFile f(mapping_file_name.Data(), "READ");

    if (!f.IsOpen())
        return false;
    TH3F *hcorrection_ly = (TH3F *)f.Get("hcorrection_ly");
    TH2F *hcorrection_cy = (TH2F *)f.Get("hcorrection_cy");
    TH2F *hcorrection_cyb = (TH2F *)f.Get("hcorrection_cyb");

    correction_mapS1 = (TH3F *)(hcorrection_ly->Clone());
    correction_mapS2 = (TH2F *)(hcorrection_cy->Clone());
    correction_mapS2b = (TH2F *)(hcorrection_cyb->Clone());

    correction_mapS1->SetDirectory(nullptr);
    correction_mapS2->SetDirectory(nullptr);
    correction_mapS2b->SetDirectory(nullptr);

    light_yield_mean = GetMapMeanValue3D(correction_mapS1);
    charge_yield_mean = GetMapMeanValue2D(correction_mapS2);
    charge_yield_mean_b = GetMapMeanValue2D(correction_mapS2b);

    vector<TString> str_qSignal = {"qS1", "qS1T", "qS1B", "qS2", "qS2T", "qS2B"};
    double coefficient;
    int powerx;
    int powery;
    int powerz;

    double meanvalue;
    for (size_t ii = 0; ii < str_qSignal.size(); ii++){
        TTree *map_tree = (TTree *)f.Get(str_qSignal[ii] + "map_Unbin3D_tree");
        map_tree->SetBranchAddress("x_min",&x_min);
        map_tree->SetBranchAddress("x_max",&x_max);
        map_tree->SetBranchAddress("y_min",&y_min);
        map_tree->SetBranchAddress("y_max",&y_max);
        map_tree->SetBranchAddress("z_min",&z_min);
        map_tree->SetBranchAddress("z_max",&z_max);
        map_tree->SetBranchAddress("powerx",&powerx);
        map_tree->SetBranchAddress("powery",&powery);
        map_tree->SetBranchAddress("powerz",&powerz);
        map_tree->SetBranchAddress("meanvalue",&meanvalue);
        map_tree->SetBranchAddress("coefficient",&coefficient);
        for(int entry = 0; entry < map_tree->GetEntries(); entry++){
            map_tree->GetEntry(entry);
            coeff[ii].push_back(coefficient);
               px[ii].push_back(powerx);
               py[ii].push_back(powery);
               pz[ii].push_back(powerz);
        }
        mean[ii] = meanvalue;
        map_tree->Delete();
    }

    cout << "Mapping file loaded." << endl;
    printf("Average charge yield = %.2f\n", charge_yield_mean);
    printf("Average light yield = %.2f\n", light_yield_mean);
    return true;
}

bool EventSelector::LoadTMcorFile() {
    TFile f(TMcor_file_name.Data(), "READ");

    if (!f.IsOpen())
        return false;

    TF1 *func_R2_cor = (TF1 *)f.Get("f_R2_cor");
    for (int i = 0; i < 3; i++) {
        double temp = func_R2_cor->GetParameter(i);
        par_R2_cor.push_back(temp);
    }
    delete func_R2_cor;

    TTree *tfactor = (TTree *)f.Get("tree");
    int nPhiBin = tfactor->GetEntries();
    SinglePhiRange = 360.0 / nPhiBin;
    for (int i = 0; i < nPhiBin; i++) {
        func_phi_cor.emplace_back((TF1 *)f.Get(Form("fit_factor%d", i)));
    }
    delete tfactor;
    cout << "TMcor file loaded." << endl;
    f.Close();
    return true;
}

bool EventSelector::LoadElectronLifetime() {
    ifstream elifetime_file(elifetime_file_name.Data());
    if (!elifetime_file.is_open()) {
        cout << "Electron lifetime file failed to open..." << endl;
        return false;
    }
    int run;
    float run_elifetime, run_elifetime_b;

    while (elifetime_file >> run >> run_elifetime >> run_elifetime_b) {
        elifetime_map[run] = run_elifetime * 1e3;
        elifetime_map_b[run] = run_elifetime_b * 1e3;
    }
    cout << "Electron lifetime:" << endl;
    auto elifetime = elifetime_map.find(o_runNumber);
    auto elifetime_b = elifetime_map_b.find(o_runNumber);
    if (elifetime != elifetime_map.end()) {
        printf("Total = %.2f us\n", elifetime->second * 1e-3);
        printf("Bottom = %.2f us\n", elifetime_b->second * 1e-3);
    } else {
        cout << "Electron lifetime not found for run " << o_runNumber
             << ", use default value" << endl;
    }
    return true;
}

double EventSelector::GetMapMeanValue2D(TH2F *map) {
    double sum = 0;
    Int_t nSamples = 0;
    double x, y;
    for (Int_t iX = 1; iX <= map->GetNbinsX(); ++iX) {
        for (Int_t iY = 1; iY <= map->GetNbinsY(); ++iY) {
            x = map->GetXaxis()->GetBinCenter(iX);
            y = map->GetYaxis()->GetBinCenter(iY);
            if (TMath::Sqrt(x * x + y * y) < 500) {
                sum += map->GetBinContent(iX, iY);
                ++nSamples;
            }
        }
    }
    return sum / nSamples;
}

double EventSelector::GetMapMeanValue3D(TH3F *map) {
    double sum = 0;
    Int_t nSamples = 0;
    double x, y, z;
    for (Int_t iX = 1; iX <= map->GetNbinsX(); ++iX) {
        for (Int_t iY = 1; iY <= map->GetNbinsY(); ++iY) {
            for (Int_t iZ = 1; iZ <= map->GetNbinsZ(); ++iZ) {
                x = map->GetXaxis()->GetBinCenter(iX);
                y = map->GetYaxis()->GetBinCenter(iY);
                z = map->GetZaxis()->GetBinCenter(iZ);
                if (TMath::Sqrt(x * x + y * y) < 500 && z > 120000 &&
                    z < 720000) {
                    sum += map->GetBinContent(iX, iY, iZ);
                    ++nSamples;
                }
            }
        }
    }
    return sum / nSamples;
}

void EventSelector::SetCorrectCharge() {
    auto elifetime = elifetime_map.find(*runNumber);
    auto elifetime_b = elifetime_map_b.find(*runNumber);

    float S2correction_factor_z;
    float S2correction_factor_z_b;
    float delta_t = o_dt;
    if (elifetime != elifetime_map.end()) {
        S2correction_factor_z = TMath::Exp(-delta_t / elifetime->second);
    } else {
        S2correction_factor_z = TMath::Exp(-delta_t / 800e3);
    }

    if (elifetime_b != elifetime_map_b.end()) {
        S2correction_factor_z_b = TMath::Exp(-delta_t / elifetime_b->second);
    } else {
        S2correction_factor_z_b = TMath::Exp(-delta_t / 700e3);
    }

    double S2correction_radius_factor{1.0};
    double S2correction_radius_factor_b{1.0};
    double S1correction_factor{1.0};
    double pos_x(0.0), pos_y(0.0);
    if (use_PAF_mapping) {
        pos_x = *xS2max_PAF;
        pos_y = *yS2max_PAF;
    } else if (use_cdfPAF_mapping) {
        pos_x = *xS2max_cdfPAF;
        pos_y = *yS2max_cdfPAF;
    } else if (use_TMs_mapping) {
        pos_x = *xS2max_TMs;
        pos_y = *yS2max_TMs;
    } else if (use_cdfTMs_mapping) {
        pos_x = *xS2max_cdfTMs;
        pos_y = *yS2max_cdfTMs;
    }
    S2correction_radius_factor = correction_mapS2->GetBinContent(
                                     correction_mapS2->FindBin(pos_x, pos_y)) /
                                 charge_yield_mean;

    S2correction_radius_factor_b =
        correction_mapS2b->GetBinContent(
            correction_mapS2b->FindBin(pos_x, pos_y)) /
        charge_yield_mean_b;

    S1correction_factor =
        correction_mapS1->GetBinContent(
            correction_mapS1->FindBin(pos_x, pos_y, delta_t)) /
        light_yield_mean;

    o_qS1C_max = *qS1_max / S1correction_factor;
    o_qS1TC_max = *qS1T_max / S1correction_factor;
    o_qS1BC_max = *qS1B_max / S1correction_factor;
    o_qS1C_max2 = o_qS1_max2 / S1correction_factor;
    o_qS1TC_max2 = o_qS1T_max2 / S1correction_factor;
    o_qS1BC_max2 = o_qS1B_max2 / S1correction_factor;
    o_qS2C_max = *qS2_max / S2correction_factor_z / S2correction_radius_factor;
    o_qS2BC_max =
        *qS2B_max / S2correction_factor_z_b / S2correction_radius_factor_b;
}

void EventSelector::SetArrayCorrectCharge() {
    auto elifetime = elifetime_map.find(*runNumber);
    auto elifetime_b = elifetime_map_b.find(*runNumber);

    float S2correction_factor_z;
    float S2correction_factor_z_b;
    float delta_t = o_dt;
    if (elifetime != elifetime_map.end()) {
        S2correction_factor_z = TMath::Exp(-delta_t / elifetime->second);
    } else {
        S2correction_factor_z = TMath::Exp(-delta_t / 800e3);
    }

    if (elifetime_b != elifetime_map_b.end()) {
        S2correction_factor_z_b = TMath::Exp(-delta_t / elifetime_b->second);
    } else {
        S2correction_factor_z_b = TMath::Exp(-delta_t / 700e3);
    }

    double S2correction_radius_factor{1.0};
    double S2correction_radius_factor_b{1.0};
    double S1correction_factor{1.0};
    double pos_x(0.0), pos_y(0.0);
    if (use_PAF_mapping) {
        pos_x = *xS2max_PAF;
        pos_y = *yS2max_PAF;
    } else if (use_cdfPAF_mapping) {
        pos_x = *xS2max_cdfPAF;
        pos_y = *yS2max_cdfPAF;
    } else if (use_TMs_mapping) {
        pos_x = *xS2max_TMs;
        pos_y = *yS2max_TMs;
    } else if (use_cdfTMs_mapping) {
        pos_x = *xS2max_cdfTMs;
        pos_y = *yS2max_cdfTMs;
    }
    S2correction_radius_factor = correction_mapS2->GetBinContent(
                                     correction_mapS2->FindBin(pos_x, pos_y)) /
                                 charge_yield_mean;

    S2correction_radius_factor_b =
        correction_mapS2b->GetBinContent(
            correction_mapS2b->FindBin(pos_x, pos_y)) /
        charge_yield_mean_b;

    S1correction_factor =
        correction_mapS1->GetBinContent(
            correction_mapS1->FindBin(pos_x, pos_y, delta_t)) /
        light_yield_mean;

    o_qS1C_max = *qS1_max / S1correction_factor;
    o_qS1TC_max = *qS1T_max / S1correction_factor;
    o_qS1BC_max = *qS1B_max / S1correction_factor;
    o_qS1C_max2 = o_qS1_max2 / S1correction_factor;
    o_qS1TC_max2 = o_qS1T_max2 / S1correction_factor;
    o_qS1BC_max2 = o_qS1B_max2 / S1correction_factor;
    o_qS2C_max = *qS2_max / S2correction_factor_z / S2correction_radius_factor;
    o_qS2BC_max =
        *qS2B_max / S2correction_factor_z_b / S2correction_radius_factor_b;

    for (long long i = 0; i < *nS2; i++) {
        if (isnan(o_xS2_TMs[i]) || isnan(o_yS2_TMs[i]) ||
            TMath::Abs(o_xS2_TMs[i]) > 1e3 || TMath::Abs(o_yS2_TMs[i]) > 1e3) {
            pos_y = o_yS2T_cor[i];
            pos_x = o_xS2T_cor[i];
        } else {
            pos_y = o_yS2_TMs[i];
            pos_x = o_xS2_TMs[i];
        }
        S2correction_radius_factor =
            correction_mapS2->GetBinContent(
                correction_mapS2->FindBin(pos_x, pos_y)) /
            charge_yield_mean;
        S2correction_radius_factor_b =
            correction_mapS2b->GetBinContent(
                correction_mapS2b->FindBin(pos_x, pos_y)) /
            charge_yield_mean_b;
        if (tS2[i] > *tS1_max) {
            delta_t = 4 * (float(tS2[i] - *tS1_max));
        } else {
            delta_t = 0;
        }
        if (elifetime != elifetime_map.end()) {
            S2correction_factor_z = TMath::Exp(-delta_t / elifetime->second);
        } else {
            S2correction_factor_z = TMath::Exp(-delta_t / 800e3);
        }
        if (elifetime_b != elifetime_map_b.end()) {
            S2correction_factor_z_b =
                TMath::Exp(-delta_t / elifetime_b->second);
        } else {
            S2correction_factor_z_b = TMath::Exp(-delta_t / 700e3);
        }
        o_qS2C[i] = qS2[i] / S2correction_factor_z / S2correction_radius_factor;
        o_qS2BC[i] =
            qS2B[i] / S2correction_factor_z_b / S2correction_radius_factor_b;
    }
}

void EventSelector::SetCorrectTMs() {
    if (*iS2_max == -1) {
        o_xS2max_cdfTMs_cor = o_xS2max_cdfTMs;
        o_yS2max_cdfTMs_cor = o_yS2max_cdfTMs;
        return;
    }
    double phi =
        TMath::ATan2(o_yS2max_cdfTMs, o_xS2max_cdfTMs) / TMath::Pi() * 180;
    int fitNo = (phi + 180) / SinglePhiRange;
    double factor =
        func_phi_cor[fitNo]->GetParameter(0) *
            exp(-o_dt / 1000 / func_phi_cor[fitNo]->GetParameter(1)) +
        func_phi_cor[fitNo]->GetParameter(2);
    double R2 =
        *yS2max_cdfTMs * *yS2max_cdfTMs + *xS2max_cdfTMs * *xS2max_cdfTMs;
    double R2CC = (par_R2_cor[0] * R2 + par_R2_cor[1] * R2 * R2 +
                   par_R2_cor[2] * R2 * R2 * R2) /
                  factor;

    o_xS2max_cdfTMs_cor =
        (float)TMath::Sqrt(R2CC) * TMath::Cos(phi * TMath::DegToRad());
    o_yS2max_cdfTMs_cor =
        (float)TMath::Sqrt(R2CC) * TMath::Sin(phi * TMath::DegToRad());
}


float EventSelector::CalculateUnbinCharge(float qSignal, double normx, double normy, double normz, int opt_map, int dimension){
  double qth = 0;
  if(dimension == 3){
    for (size_t jj = 0; jj < coeff[opt_map].size(); jj++){
      qth += coeff[opt_map][jj] * pow(normx,px[opt_map][jj]) * pow(normy,py[opt_map][jj]) * pow(normz,pz[opt_map][jj]);
    }
  }
  else if (dimension == 2){
    for (size_t jj = 0; jj < coeff[opt_map].size(); jj++){
      qth += coeff[opt_map][jj] * pow(normx,px[opt_map][jj]) * pow(normy,py[opt_map][jj]);
    }
  }
  double qSC = qSignal*mean[opt_map]/(qth+mean[opt_map]); 
  float qSC_float = qSC;
  return qSC_float;
}


void EventSelector::SetCorrectCharge_Unbin() {
    auto elifetime = elifetime_map.find(*runNumber);
    auto elifetime_b = elifetime_map_b.find(*runNumber);
    float S2correction_factor_z;
    float S2correction_factor_z_b;
    float delta_t = o_dt;
    if (elifetime != elifetime_map.end()) {
        S2correction_factor_z = TMath::Exp(-delta_t / elifetime->second);
    } else {
        S2correction_factor_z = TMath::Exp(-delta_t / 800e3);
    }

    if (elifetime_b != elifetime_map_b.end()) {
        S2correction_factor_z_b = TMath::Exp(-delta_t / elifetime_b->second);
    } else {
        S2correction_factor_z_b = TMath::Exp(-delta_t / 700e3);
    }

    double pos_x(0.0), pos_y(0.0), pos_z(0.0);
    double normx(0.0), normy(0.0), normz(0.0);
    if (use_PAF_mapping) {
        pos_x = *xS2max_PAF;
        pos_y = *yS2max_PAF;
    } else if (use_cdfPAF_mapping) {
        pos_x = *xS2max_cdfPAF;
        pos_y = *yS2max_cdfPAF;
    } else if (use_TMs_mapping) {
        pos_x = *xS2max_TMs;
        pos_y = *yS2max_TMs;
    } else if (use_cdfTMs_mapping) {
        pos_x = *xS2max_cdfTMs;
        pos_y = *yS2max_cdfTMs;
    }
    pos_z = delta_t/1000.;
    normx = (2*pos_x-x_min-x_max)/(x_max-x_min);
    normy = (2*pos_y-y_min-y_max)/(y_max-y_min);
    normz = (2*pos_z-z_min-z_max)/(z_max-z_min);

    o_qS1_C   = CalculateUnbinCharge(*qS1_max   , normx, normy, normz, 0, 3);
    o_qS1T_C  = CalculateUnbinCharge(*qS1T_max  , normx, normy, normz, 1, 3);
    o_qS1B_C  = CalculateUnbinCharge(*qS1B_max  , normx, normy, normz, 2, 3);
    o_qS1_C2  = CalculateUnbinCharge(o_qS1_max2 , normx, normy, normz, 0, 3);
    o_qS1T_C2 = CalculateUnbinCharge(o_qS1T_max2, normx, normy, normz, 1, 3);
    o_qS1B_C2 = CalculateUnbinCharge(o_qS1B_max2, normx, normy, normz, 2, 3);
    o_qS2_C   = CalculateUnbinCharge(*qS2_max  / S2correction_factor_z  , normx, normy, normz, 3, 3);
    //There is no need to correct qS2T
    o_qS2B_C  = CalculateUnbinCharge(*qS2B_max / S2correction_factor_z_b, normx, normy, normz, 5, 3);
}


void EventSelector::SetArrayCorrectCharge_Unbin() {
    auto elifetime = elifetime_map.find(*runNumber);
    auto elifetime_b = elifetime_map_b.find(*runNumber);
    float S2correction_factor_z;
    float S2correction_factor_z_b;
    float delta_t = o_dt;
    if (elifetime != elifetime_map.end()) {
        S2correction_factor_z = TMath::Exp(-delta_t / elifetime->second);
    } else {
        S2correction_factor_z = TMath::Exp(-delta_t / 800e3);
    }

    if (elifetime_b != elifetime_map_b.end()) {
        S2correction_factor_z_b = TMath::Exp(-delta_t / elifetime_b->second);
    } else {
        S2correction_factor_z_b = TMath::Exp(-delta_t / 700e3);
    }

    double pos_x(0.0), pos_y(0.0), pos_z(0.0);
    double normx(0.0), normy(0.0), normz(0.0);
    if (use_PAF_mapping) {
        pos_x = *xS2max_PAF;
        pos_y = *yS2max_PAF;
    } else if (use_cdfPAF_mapping) {
        pos_x = *xS2max_cdfPAF;
        pos_y = *yS2max_cdfPAF;
    } else if (use_TMs_mapping) {
        pos_x = *xS2max_TMs;
        pos_y = *yS2max_TMs;
    } else if (use_cdfTMs_mapping) {
        pos_x = *xS2max_cdfTMs;
        pos_y = *yS2max_cdfTMs;
    }
    pos_z = delta_t/1000.;
    normx = (2*pos_x-x_min-x_max)/(x_max-x_min);
    normy = (2*pos_y-y_min-y_max)/(y_max-y_min);
    normz = (2*pos_z-z_min-z_max)/(z_max-z_min);

    o_qS1_C   = CalculateUnbinCharge(*qS1_max   , normx, normy, normz, 0, 3);
    o_qS1T_C  = CalculateUnbinCharge(*qS1T_max  , normx, normy, normz, 1, 3);
    o_qS1B_C  = CalculateUnbinCharge(*qS1B_max  , normx, normy, normz, 2, 3);
    o_qS1_C2  = CalculateUnbinCharge(o_qS1_max2 , normx, normy, normz, 0, 3);
    o_qS1T_C2 = CalculateUnbinCharge(o_qS1T_max2, normx, normy, normz, 1, 3);
    o_qS1B_C2 = CalculateUnbinCharge(o_qS1B_max2, normx, normy, normz, 2, 3);
    o_qS2_C   = CalculateUnbinCharge(*qS2_max  / S2correction_factor_z  , normx, normy, normz, 3, 3);
    //There is no need to correct qS2T
    o_qS2B_C  = CalculateUnbinCharge(*qS2B_max / S2correction_factor_z_b, normx, normy, normz, 5, 3);

    for (long long i = 0; i < *nS2; i++) {
        if (isnan(o_xS2_TMs[i]) || isnan(o_yS2_TMs[i]) ||
            TMath::Abs(o_xS2_TMs[i]) > 1e3 || TMath::Abs(o_yS2_TMs[i]) > 1e3) {
            pos_y = o_yS2T_cor[i];
            pos_x = o_xS2T_cor[i];
        } else {
            pos_y = o_yS2_TMs[i];
            pos_x = o_xS2_TMs[i];
        }
        if (tS2[i] > *tS1_max) {
            delta_t = 4 * (float(tS2[i] - *tS1_max));
        } else {
            delta_t = 0;
        }
        if (elifetime != elifetime_map.end()) {

            S2correction_factor_z = TMath::Exp(-delta_t / elifetime->second);
        } else {
            S2correction_factor_z = TMath::Exp(-delta_t / 800e3);
        }
        if (elifetime_b != elifetime_map_b.end()) {
            S2correction_factor_z_b =
                TMath::Exp(-delta_t / elifetime_b->second);
        } else {
            S2correction_factor_z_b = TMath::Exp(-delta_t / 700e3);
        }
        o_qS2C[i]  = CalculateUnbinCharge(qS2[i]  / S2correction_factor_z  , normx, normy, normz, 3, 3);
        //There is no need to correct qS2T
        o_qS2BC[i] = CalculateUnbinCharge(qS2B[i] / S2correction_factor_z_b, normx, normy, normz, 5, 3);
    }
}


bool EventSelector::LoadPolRankFile() {
    ifstream polrank_file(polrank_file_name.Data());
    if (!polrank_file.is_open()) {
        cerr << "Error: polrank file failed to open, plz check!" << endl;
        return false;
    }
    string line;
    while (getline(polrank_file, line)) {
        stringstream ss(line);
        vector<double> pars;
        double par;
        while(ss>>par){
            pars.push_back(par);
        }
        int run = pars[0];
        unsigned bit = 1;
        while (bit < pars.size()){
            tsegment_map[run].push_back( {pars[bit], pars[bit+1]} );
            int rank1 = pars[bit+2];
            int rank2 = pars[bit+3];
            vector<double> rank1_vec, rank2_vec;
            for(auto ii = 0; ii <= rank1; ii++){
                rank1_vec.push_back(pars[bit+4+ii]);
            }
            rank1_map[run].push_back(rank1_vec);
            for(auto ii = 0; ii <= rank2; ii++){
                rank2_vec.push_back(pars[bit+5+rank1+ii]);
            }
            rank2_map[run].push_back(rank2_vec);
            bit += rank1 + rank2 + 6;
            rank1_vec.clear();
            rank2_vec.clear();
        }
    }
    if ( tsegment_map.find(o_runNumber) != tsegment_map.end() ) {
        cout<<"\nrun "<<o_runNumber<<" found\n";
        cout<<"Segments in hour: ";
        for(size_t ii = 0; ii < tsegment_map[o_runNumber].size();ii++){
            cout<<"{"<<tsegment_map[o_runNumber][ii][0]<<", "<<tsegment_map[o_runNumber][ii][1]<<"}\t";
        }
        cout<<endl;
    } else{
        cerr << "Warning: run" << o_runNumber << " was not found in polrank file,";
        cerr << "Using un-stretched values\n";
    }
    return true;
}


void EventSelector::StretchS1S2(){
    const double stdS1 = 34e3;//streching reference value, which is somewhat arbitrary
    const double stdS2 = 15e3;
    //set the default values
    o_factor1 = 1;
    o_factor2 = 1;
    o_qS1_Cs  = o_qS1_C  * o_factor1;
    o_qS2B_Cs = o_qS2B_C * o_factor2;
    o_qS1C_maxs  = o_qS1C_max  * o_factor1;
    o_qS2BC_maxs = o_qS2BC_max * o_factor2;

    double th = o_t*4e-9/3600.;
    int Nsegments = tsegment_map[o_runNumber].size();//At most case, this value is equal to one, except 2 runs.
    for(int iteration = 0; iteration < Nsegments; iteration++){
        double runTime_bgn = tsegment_map[o_runNumber][iteration][0];
        double runTime_end = tsegment_map[o_runNumber][iteration][1];
        if (th < runTime_bgn || th > runTime_end){//not in the stretching time range
            continue;
        }
        int Npars1 = rank1_map[o_runNumber][iteration].size();//Number of function parameters
        int Npars2 = rank2_map[o_runNumber][iteration].size();
        TF1 *fpol1 = new TF1("fpol1",Form("pol%d",Npars1-1));//maxpower is Npars-1
        for(int power = 0; power < Npars1; power++){
            fpol1->SetParameter(power,rank1_map[o_runNumber][iteration][power]);
        }
        TF1 *fpol2 = new TF1("fpol2",Form("pol%d",Npars2-1));//maxpower is Npars-1
        for(int power = 0; power < Npars2; power++){
            fpol2->SetParameter(power,rank2_map[o_runNumber][iteration][power]);
        }
        o_factor1 = stdS1 / fpol1->Eval(th);
        o_factor2 = stdS2 / fpol2->Eval(th);
	o_qS1_Cs  = o_qS1_C  * o_factor1;
        o_qS2B_Cs = o_qS2B_C * o_factor2;
        o_qS1C_maxs  = o_qS1C_max  * o_factor1;
        o_qS2BC_maxs = o_qS2BC_max * o_factor2;
        break;
    }
}

