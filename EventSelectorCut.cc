#include "EventSelector.hh"
#include <limits>
// test
bool EventSelector::ApplyQualityCut(bool store_whole_data_flag) {
    if (BasicCut(store_whole_data_flag))
        return true;
    S1PerPmtCut(*iS1_max);
    S1PatternCut(*iS1_max);
    S1AsyCut(*iS1_max);
    S2ShapeCut(*iS2_max);
    S2AsyCut(*iS2_max);
    S2TBACut_Unify(*iS2_max);
    GasCut(*iS2_max);
    DrCut();
    WallCut();
    DiffusionCut(*iS2_max);
    Deadtime_enhance();
    SSCut();
    FVCut();
    CalculateNPostS1();
    CalculateNPostS2();
    return false;
}

bool EventSelector::BasicCut(bool store_whole_data_flag) {
    if (store_whole_data_flag) {
        if (!( *iS1_max >= 0 && *iS2_max >= 0 &&
              4e-3 * (double(*tS2_max - *tS1_max)) > 0 &&
              4e-3 * (double(*tS2_max - *tS1_max)) < 1000 &&
              (*yS2max_TMs * *yS2max_TMs + *xS2max_TMs * *xS2max_TMs) < 400e3 &&
              (*qS1_max + *qS2_max) / *qTotal > 0.12 && nPMTS1[*iS1_max] > 1)) {
            o_basicCut = false;
            return true;
        }
        return false;
    } else { // daily evolution use only
        if (!(*iS1_max >= 0 && *iS2_max >= 0 && *qS1_max >= 3 &&
              *qS1_max < 400 && *qS2_max > 80 && *qS2_max < 20000 &&
              !*deadtime && 4e-3 * (double(*tS2_max - *tS1_max)) > 20 &&
              4e-3 * (double(*tS2_max - *tS1_max)) < 770 &&
              (*yS2max_TMs * *yS2max_TMs + *xS2max_TMs * *xS2max_TMs) < 400e3 &&
              (*qS1_max + *qS2_max) / *qTotal > 0.12 && *ratioTSignal < 0.2 &&
              *qElse < 3000 && nPMTS1[*iS1_max] > 1)) {
            o_basicCut = false;
            return true;
        }
        return false;
    }
}

bool EventSelector::Deadtime_enhance() {
    if (!(!*deadtime && (*tLargeSignal * 4e-6 > 22 || *tLargeSignal == 0) &&
          (*qTotalPreEvent < 100 && *tDiffPreEvent * 4e-6 > 1) &&
          *tLargeSignal * 4e-9 < 2)) {
        o_deadtime_enhanceCut = false;
        return true;
    }
    return false;
}

bool EventSelector::FVCut() {
    if (!((*yS2max_TMs * *yS2max_TMs + *xS2max_TMs * *xS2max_TMs) < 250e3 &&
          4e-3 * (double(*tS2_max - *tS1_max)) > 20 &&
          4e-3 * (double(*tS2_max - *tS1_max)) < 770 &&
          *yS2max_TMs * *yS2max_TMs + *xS2max_TMs * *xS2max_TMs <
              250e3 -
                  (140 - 4e-3 * (double(*tS2_max - *tS1_max))) / 140 * 60e3)) {
        o_fv_extendCut = false;
        return true;
    }
    return false;
}

void EventSelector::CalculateNPostS1() {
    o_nPostS1 = 0;
    o_nGoodS1 = 0;
    int i = -1;
    while (i < *nS1 && 0 < *nS1) {
        ++i;
        if (i == *nS1)
            break;
        if (S1PerPmtCut(i) || S1PatternCut(i))
            continue;
        if (tS1[i] + 750 < *tS2_max && nPMTS1[i] > 1 && hS1[i] > 0.5)
            ++o_nGoodS1;
        if (!S1AsyCut(i))
            ++o_nPostS1;
    }
}

void EventSelector::CalculateNPostS2() {
    o_nPostS2 = 0;
    o_nRealPostS2 = 0;
    int i = -1;
    while (i < *nS2 && 0 < *nS2) {
        ++i;
        if (i == *nS2)
            break;
        if (qS2[i] <= 0.06 * (*qS2_max) || qS2[i] < 75 || wS2[i] < 200)
            continue;
        ++o_nPostS2;
        if (S2ShapeCut(i) || S2TBACut_Unify(i) || GasCut(i))
            continue;
        o_iGoodS2[o_nRealPostS2] = i;
        ++o_nRealPostS2;
    }
}

bool EventSelector::S1PerPmtCut(int i) {
    if (!(qS1[i] / nPMTS1[i] < 1.4847 + exp(-0.08 * qS1[i]) + 0.004 * qS1[i])) {
        if (i == *iS1_max)
            o_S1PerPmtCut = false;
        return true;
    }
    return false;
}

bool EventSelector::S1PatternCut(int i) {
    if (!(qS1BmaxHitCharge[i] < 3 + 0.05 * qS1[i] &&
          qS1TmaxHitCharge[i] < 3 + 0.05 * qS1[i])) {
        if (i == *iS1_max)
            o_S1PatternCut = false;
        return true;
    }
    return false;
}

bool EventSelector::S2ShapeCut(int i) {
    if (!(ratioqS2PrePeakSmr[i] > 0.1 && ratioqS2PrePeakSmr[i] < 0.86)) {
        if (i == *iS2_max)
            o_S2ShapeCut = false;
        return true;
    }
    return false;
}

bool EventSelector::GasCut(int i) {
    if (qS2[i] / wS2CDF[i] / hS2[i] <= 0.6 - 2000 / qS2[i]) {
        o_gas_s2Cut = false;
        return true;
    }
    return false;
}

bool EventSelector::S1AsyCut(int i) {
    if (tS1[i] >= *tS2_max) {
        if (i == *iS1_max) {
            o_S1AsyCut = false;
        }
        return true;
    }
    if (!((qS1T[i] - qS1B[i]) / qS1[i] <
              exp(-(4e-3 * (double(*tS2_max - tS1[i])) - 400) / 700) - 0.75 &&
          (qS1T[i] - qS1B[i]) / qS1[i] >
              exp(-(4e-3 * (double(*tS2_max - tS1[i])) - 400) / 800) - 2.21)) {
        if (i == *iS1_max)
            o_S1AsyCut = false;
        return true;
    }
    if (!(tS1[i] + 1e3 < tS1[*iS1_max] ||
          (tS1[i] > tS1[*iS1_max] + 10e3 && tS1[i] + 1e3 < *tS2_max)) &&
        i != *iS1_max)
        return true;
    return false;
}

bool EventSelector::S2AsyCut(int i) {
    if (!(qS2T[i] / (qS2B[i] + 1) >= 0.4 && qS2T[i] / (qS2B[i] + 1) <= 6)) {
        if (i == *iS2_max)
            o_S2AsyCut = false;
        return true;
    }
    return false;
}

bool EventSelector::S2TBACut(int i) {
        if (!((qS2T[i] - qS2B[i]) / qS2[i] <
              0.576346 + 0.1 * exp(-qS2[i] / 500) + (-1.2e-6 * qS2[i]) &&
          (qS2T[i] - qS2B[i]) / qS2[i] >
              0.96 *
                  (0.45898457 - 0.2 * exp(-qS2[i] / 800) + (-8e-6 * qS2[i])))) {
        if (i == *iS2_max)
            o_S2TBACut = false;
        return true;
    }
    return false;
}

bool EventSelector::S2TBACut_Loose(int i) {
    if (!((qS2T[i] - qS2B[i]) / qS2[i] <
          0.6 + 0.1 * exp(-qS2[i] / 500) + (-1.2e-6 * qS2[i]) &&
          (qS2T[i] - qS2B[i]) / qS2[i] >
          0)) {
        if (i == *iS2_max)
            o_S2TBACut = false;
        return true;
    }
    return false;
}

bool EventSelector::NearOffPMTCut(int i) {
//        if (!((yS2T_cor[i]<-xS2T_cor[i]+300 && xS2T_cor[i]<0&& yS2T_cor[i] >
//        -120&& yS2T_cor[i] > - xS2T_cor[i] - 500)||(pow((yS2T_cor[i] -
//        125.92), 2) + pow((xS2T_cor[i] - 387.56), 2) <
//        5806.44)||(pow((yS2T_cor[i] + 42.6), 2) + pow((xS2T_cor[i] - 405.27),
//        2) < 5806.44)||(pow((yS2T_cor[i] + 329.67), 2) + pow((xS2T_cor[i] +
//        239.52), 2) < 5806.44))){
    if (!((yS2_cdfTMs[i] < -xS2_cdfTMs[i] + 300 && xS2_cdfTMs[i] < 0 &&
           yS2_cdfTMs[i] > -120 && yS2_cdfTMs[i] > -xS2_cdfTMs[i] - 500) ||
          (pow((yS2_cdfTMs[i] - 125.92), 2) + pow((xS2_cdfTMs[i] - 387.56), 2) <
           5806.44) ||
          (pow((yS2_cdfTMs[i] + 42.6), 2) + pow((xS2_cdfTMs[i] - 405.27), 2) <
           5806.44) ||
          (pow((yS2_cdfTMs[i] + 329.67), 2) + pow((xS2_cdfTMs[i] + 239.52), 2) <
           5806.44))) {    
	return true;
    }
    return false;
}

bool EventSelector::S2TBACut_Unify(int i) {
    if (NearOffPMTCut(i))
        return S2TBACut(i);
    else
        return S2TBACut_Loose(i);
}

bool EventSelector::DrCut() {
    if (!(sqrt(pow((*xS2Tcor_max - *xS2max_TM), 2) +
               pow((*yS2Tcor_max - *yS2max_TM), 2)) < 100)) {
        o_drCut = false;
        return true;
    }
    return false;
}

bool EventSelector::WallCut() {
    if (!(*rms_TM < 300 && *rms_TM > 177.6527 - 40 * exp(-(*qS2_max)/500))) {
        o_wallCut = false;
        return true;
    }
    return false;
}

bool EventSelector::DiffusionCut(int i) {
    if (tS2[i] <= *tS1_max) {
        if (i == *iS2_max) {
            o_diffusion_enhanceCut = false;
        }
        return true;
    }
    if (!(4e-3 * wS2CDF[i] >
              2.5631 *
                  sqrt(3.949e-2 +
                       (2 *
                        (2.425e-3 + (-2.226e-3) * exp(qS2[i] / (-5.863e+2))) *
                        4e-3 * (double(tS2[i] - *tS1_max))) /
                           1.411 / 1.411) &&
          4e-3 * wS2CDF[i] <
              2.5631 * (0.2 + 0.1 * (1 / (exp((qS2[i] - 2500) / 500) + 1)) +
                        sqrt(2 * 0.0040 * 4e-3 * (double(tS2[i] - *tS1_max))) /
                            1.411))) {
        if (i == *iS2_max)
            o_diffusion_enhanceCut = false;
        return true;
    }
    return false;
}

bool EventSelector::SSCut() {
    int count{0};
    for (int i = 0; i < *nS2; ++i) {
        if (qS2[i] < 25 || wS2[i] < 200 || S2ShapeCut(i) || S2TBACut(i) ||
            GasCut(i))
            continue;
        if (qS2[i] > 0.08 * (*qS2_max))
            ++count;
        else {
            if (tS2[i] > *tS2_max - 800 && tS2[i] < *tS2_max + 2500) {
                if (qS2[i] > 200)
                    count++;
            } else {
                if (qS2[i] > 70)
                    count++;
            }
        }
    }
    if (!(count == 1)) {
        o_ssCut = false;
        return true;
    }
    return false;
}

bool EventSelector::EnergyCut() {
    if (o_qS1_max < 2)
        return true;
    if (o_qS1_max > 200)
        return true;
    if (o_qS2_max < 80)
        return true;
    if (o_qS2_max > 20000)
        return true;
    return false;
}

bool EventSelector::NRCut() {
    if (log10(o_qS2C_max / o_qS1C_max) >
        1.88478 + 0.643742 * exp(-o_qS1C_max / 6.75319) +
            (-0.00288991) * o_qS1C_max)
        return true;
    return false;
}
