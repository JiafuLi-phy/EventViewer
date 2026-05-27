#include "Esum.hh"

Esum::Esum(PandaXDataSource& pds, uint32_t run_no)
    : pmt_map(pds.loadPmtMap(run_no))
{}

CalibData Esum::operator() (const CalibData &cd)
{
  //  std::cout<<"cluster"<<cd.startTime<<" "<<cd.endTime<<std::endl;
    CalibData edata;
    edata.runNumber = cd.runNumber;
    edata.groupNumber = cd.groupNumber;
    edata.startTime = cd.startTime;
    edata.endTime = cd.endTime;
    uint64_t sampleNumber = cd.endTime - cd.startTime;
    CalibPmtSegment topW, bottomW, vetoW;
    topW.startTime = cd.startTime;
    topW.peValue.resize(sampleNumber);
    topW.channelNumber = 90001;
    bottomW.startTime = cd.startTime;
    bottomW.peValue.resize(sampleNumber);
    bottomW.channelNumber = 90002;
    vetoW.startTime = cd.startTime;
    vetoW.peValue.resize(sampleNumber);
    vetoW.channelNumber = 90003;

    for (const auto &cw: cd.segments) {
      //      std::cout<<cw.startTime<<" "<<cw.startTime+cw.peValue.size()<<std::endl;
      //       for(const auto &e: cw.peValue) {
      //	  if (e>1e5||e<-1e5)
      //    	std::cout<<e<<std::endl;
      //          }
        auto pinfo = pmt_map.find(cw.channelNumber);
        if (pinfo == pmt_map.end()) {
            continue;
        }
        if (pinfo->second.gainType == "low_gain")
            continue;
        const auto& array = pinfo->second.pmtarray;
        if (array == "TopMain") {
            add_segments(topW, cw);
        } else if (array == "BottomMain") {
            add_segments(bottomW, cw);
        } else if (array == "TopVeto" || array == "BottomVeto") {
            add_segments(vetoW, cw);
        } else {
            continue;
        }
    }
    //        for(const auto &e : topW.peValue) {
    //          std::cout<<e<<std::endl;
    //        }
    edata.segments.push_back(std::move(topW));
    edata.segments.push_back(std::move(bottomW));
    edata.segments.push_back(std::move(vetoW));

    return edata;
}

void Esum::add_segments(CalibPmtSegment & dst, const CalibPmtSegment & seg)
{
  uint64_t t0, tx;
  if (seg.startTime>dst.startTime) {
    t0 = seg.startTime-dst.startTime;
    tx = 0;
  }
  else {
    t0 = 0;
    tx = dst.startTime-seg.startTime;
  }
  //  std::cout<<seg.startTime<<" "<<seg.endTime<<" "<<dst.startTime<<std::endl;
  //  std::cout<<t0<<" "<<tx<<std::endl;
  uint64_t t1 = t0 + seg.peValue.size() -tx ;
  if (t1 > (uint64_t)dst.peValue.size()) {
    t1 = dst.peValue.size();
  }
  std::transform(dst.peValue.begin()+t0, dst.peValue.begin()+t1, seg.peValue.begin()+tx, dst.peValue.begin()+t0, std::plus<float>());
}
