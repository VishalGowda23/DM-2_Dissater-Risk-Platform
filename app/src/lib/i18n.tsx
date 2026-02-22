import { createContext, useContext, useState, type ReactNode } from 'react';

export type Lang = 'en' | 'hi' | 'mr';

// ─────────────────────────────────────────────────────────────────────────────
// Translation dictionary
// ─────────────────────────────────────────────────────────────────────────────
export const translations = {
  en: {
    // ── App header ──────────────────────────────────────────────────────────
    appName: 'PRAKALP',
    appSubtitle: 'Predictive Risk Assessment & Knowledge Analytics',
    live: 'LIVE',
    updated: 'Updated',
    refresh: 'Refresh',
    ingest: 'Ingest',
    calculate: 'Calculate',

    // ── Tabs ─────────────────────────────────────────────────────────────────
    tabRiskMap: 'Risk Map',
    tabSummary: 'Summary',
    tabOptimizer: 'Optimizer',
    tabScenarios: 'Scenarios',
    tabForecast: 'Forecast',
    tabValidation: 'Validation',
    tabAlerts: 'Alerts',
    tabEvacuation: 'Evacuation',
    tabCommand: 'Command',

    // ── Map panel labels ──────────────────────────────────────────────────────
    wardRankings: 'Ward Rankings',
    wardDetails: 'Ward Details',

    // ── Footer ────────────────────────────────────────────────────────────────
    dataSources: 'Data Sources',
    openMeteo: 'Open-Meteo API',
    pmcWard: 'PMC Ward Data',
    census: 'Census 2011',

    // ── Evacuation Map ────────────────────────────────────────────────────────
    evacTitle: 'Evacuation Route Optimizer',
    evacSubtitle: 'Safe routes to nearest shelters, dynamically avoiding flood-prone roads',
    computeRoutes: 'Compute Routes',
    allRoutes: 'All Routes',
    floodSim: 'Flood Sim',
    sos: 'SOS',
    emergencyBroadcast: 'EMERGENCY BROADCAST ACTIVE',
    elapsed: 'Elapsed',
    peopleEvacuating: 'People evacuating',
    highRiskWards: 'High-risk wards',
    endBroadcast: 'END BROADCAST',
    totalWards: 'Total Wards',
    shelters: 'Shelters',
    immediate: 'Immediate',
    avgWalk: 'Avg Walk',
    wardRoutes: 'Ward Routes',
    recommendedShelter: 'Recommended Shelter',
    alternativeShelters: 'Alternative Shelters',
    allShelters: 'All Shelters',
    distance: 'Distance',
    walking: 'Walking',
    routeSafety: 'Route Safety',
    capacity: 'Capacity',
    walkingEta: 'Walking ETA',
    estimatedFillRate: 'Est. fill rate',
    avoidFloodProne: 'Avoid (flood-prone)',
    useInstead: 'Use instead',
    clickWard: 'Click a ward on the map or list to view its evacuation route',
    routesAnimateRealtime: 'Routes animate in real-time on the map',
    evacuateNow: 'EVACUATE NOW',
    prepare: 'PREPARE',
    monitor: 'MONITOR',
    standby: 'STANDBY',
    safe: 'safe',
    moderateRiskStatus: 'moderate risk',
    unsafeStatus: 'unsafe',
    type: 'Type',
    riskLabel: 'Risk',
    riskLevel: 'Risk Level',

    // ── Legend ────────────────────────────────────────────────────────────────
    legend: 'Legend',
    highRiskWard: 'High Risk Ward',
    mediumRisk: 'Medium Risk',
    lowRisk: 'Low Risk',
    recShelter: 'Recommended Shelter',
    altShelter: 'Alt Shelter',
    otherShelter: 'Other Shelter',
    activeRoute: 'Active Route',
    otherRoutes: 'Other Routes',

    // ── Risk Summary ──────────────────────────────────────────────────────────
    noRiskData: 'No risk data available',
    cityRiskSummary: 'City Risk Summary',
    puneMunicipal: 'Pune Municipal Corporation',
    overallStatus: 'Overall Status',
    totalPopulation: 'Total Population',
    criticalWards: 'Critical Wards',
    highRiskWardsLabel: 'High Risk Wards',
    riskDistribution: 'Risk Distribution',
    avgRiskByHazard: 'Average Risk by Hazard',
    floodRisk: 'Flood Risk',
    heatRisk: 'Heat Risk',
    top10Wards: 'Top 10 Highest Risk Wards',
    rank: 'Rank',
    ward: 'Ward',
    topHazard: 'Top Hazard',
    riskScore: 'Risk Score',
    population: 'Population',
    statusNormal: 'NORMAL',
    statusHigh: 'HIGH',
    statusCritical: 'CRITICAL',

    // ── Resource Optimizer ────────────────────────────────────────────────────
    resourceConfig: 'Resource Configuration',
    prioritizeSurging: 'Prioritize surging wards',
    prioritizeSurgingOn: 'ON — wards with rapidly rising risk get extra weight, even if absolute risk is still low',
    prioritizeSurgingOff: 'OFF — allocate purely by current risk × population',
    runOptimization: 'Run Optimization',
    noDeployRequired: 'No Deployment Required',
    noDeployDesc: 'All ward risk scores are currently below the activation threshold',
    highestNeed: 'Highest Need',
    deployed: 'Deployed',
    unitsAllocated: 'units allocated',
    allocationSummary: 'Allocation Summary by Resource Type',
    allocated: 'allocated',
    resourceGapAnalysis: 'Resource Gap Analysis',
    overallCoverage: 'Overall coverage',
    totalNeeded: 'Total needed',
    totalAvailable: 'Total available',
    deficit: 'DEFICIT',
    available: 'Available',
    required: 'Required',
    sufficient: 'Sufficient',
    wardwiseAllocations: 'Ward-wise Allocations',
    allocationRationale: 'Allocation Rationale',
    needScore: 'Need Score',

    // ── Scenario Simulator ────────────────────────────────────────────────────
    quickPresets: 'Quick Presets',
    baseline: 'Baseline',
    scenario: 'Scenario',
    floodRiskChange: 'Flood Risk Change',
    heatRiskChange: 'Heat Risk Change',
    highImpactScenario: 'High Impact Scenario',
    newlyCriticalWards: 'Newly Critical Wards',
    noChange: 'NO CHANGE',
    riskChangeByWard: 'Risk Change by Ward (Top 10)',
    detailedWardImpact: 'Detailed Ward Impact',
    status: 'Status',

    // ── Forecast ─────────────────────────────────────────────────────────────
    riskTimeline: 'Risk Timeline (48 Hours)',
    selectWardForecast: 'Select a ward to view forecast timeline',
    totalWardsLabel: 'Total Wards',
    peakRisk: 'Peak Risk',
    dangerWindow: 'Danger Window',
    reachingCritical: 'Reaching Critical',
    riskRising: 'Risk Rising',
    hourlyDetail: 'Hourly Detail',

    // ── Historical Validation ─────────────────────────────────────────────────
    selectHistoricalEvent: 'Select a historical event to validate',
    modelTestedDesc: 'The model will be tested against real weather data from that event',
    runningValidation: 'Running validation against historical data...',
    accuracy: 'Accuracy',
    precision: 'Precision',
    recall: 'Recall',
    leadTime: 'Lead Time',
    predicted: 'Predicted',
    actuallyHit: 'Actually Hit',
    result: 'Result',
    correctlyFlagged: 'Correctly flagged as at-risk',
    wardLevelPredictions: 'Ward-Level Predictions vs Actual',

    // ── Alerts ────────────────────────────────────────────────────────────────
    alertsSubtitle: 'Real-time bilingual alerts for citizens and authorities',
    recommendedActions: 'Recommended Actions:',

    // ── Risk Map ─────────────────────────────────────────────────────────────
    wardId: 'Ward ID:',
    riskScoreLabel: 'Risk Score:',
    topHazardLabel: 'Top Hazard:',
    floodLabel: 'Flood:',
    heatLabel: 'Heat:',
    populationLabel: 'Population:',
    openStreetMap: 'OpenStreetMap',

    // ── Ward Detail ───────────────────────────────────────────────────────────
    selectWardDetail: 'Select a ward to view details',
    clickWardHint: 'Click on a ward in the list or map',
    recommendations: 'Recommendations',
    eventCurrent: 'Event (Current)',
    baselineLabel: 'Baseline',
    areaLabel: 'Area:',
    densityLabel: 'Density:',
    elevLabel: 'Elev:',
    popLabel: 'Pop:',

    // ── Decision Support ─────────────────────────────────────────────────────
    commandCenter: 'COMMAND CENTER',
    situationLevel: 'Situation Level',
    populationAtRisk: 'Population at Risk',
    readiness: 'Readiness',
    totalActions: 'Total Actions',
    criticalPending: 'Critical Pending',
    allClear: 'All Clear',
    noActionsRequired: 'No actions required at current risk levels',
    impact: 'Impact:',
    why: 'Why:',

    // ── Risk Level Labels ─────────────────────────────────────────────────────
    low030: 'Low (0-30%)',
    moderate3160: 'Moderate (31-60%)',
    high6180: 'High (61-80%)',
    critical81100: 'Critical (81-100%)',

    // ── Ward Detail extended ──────────────────────────────────────────────────
    riskComparison: 'Risk Comparison',
    vsBaseline: 'vs Baseline',
    aboveBaseline: 'above baseline',
    belowBaseline: 'below baseline',
    riskExplanation: 'Risk Explanation',
    topContribFactors: 'Top Contributing Factors',
    floodBtn: 'Flood',
    heatBtn: 'Heat',

    // ── Resource Optimizer extended ───────────────────────────────────────────
    highestRecordedRisk: 'Highest recorded risk:',
    noDeployUntilDeter: 'No resources will be deployed until risk conditions deteriorate.',

    // ── Scenario extended ─────────────────────────────────────────────────────
    floodDeltaHeader: 'Flood Δ',
    heatDeltaHeader: 'Heat Δ',
    statusIncreased: 'INCREASED',
    statusReduced: 'REDUCED',
    statusHighImpact: 'HIGH IMPACT',
    statusNewCritical: 'NEW CRITICAL',

    // ── Forecast extended ─────────────────────────────────────────────────────
    criticalLine: 'Critical',
    highLine: 'High',
    floodRiskName: 'Flood Risk',
    heatRiskName: 'Heat Risk',
    criticalInHours: 'Critical in',
    populationStat: 'Population',
    baselineFloodStat: 'Baseline Flood',
    baselineHeatStat: 'Baseline Heat',

    // ── Historical Validation extended ────────────────────────────────────────
    modelWouldPredict: 'Model WOULD have predicted',
    modelMayMiss: 'Model may have missed',
    avgRiskForWards: 'Average risk for affected wards',
    leadTimeStat: 'Lead time',
    hoursBeforeEvent: 'hours before event',
    truePosTitle: 'True Positives',
    falseNegTitle: 'False Negatives',
    missedActually: 'Missed — actually affected',
    wardByWardAnalysis: 'Ward-by-Ward Analysis',
    yesLabel: 'Yes',

    // ── Alerts extended ───────────────────────────────────────────────────────
    alertPanelTitle: 'Alert System — SMS / WhatsApp Integration',
    generateAlerts: 'Generate Alerts',
    citizenAlertsLabel: 'Citizen Alerts',
    authorityAlertsLabel: 'Authority / PMC Alerts',
    noAuthorityAlerts: 'No authority-level alerts at current risk levels',
    alertTotal: 'TOTAL',
    alertEmergency: 'EMERGENCY',
    alertWarning: 'WARNING',
    alertWatch: 'WATCH',
    alertAdvisory: 'ADVISORY',
    sendToPhone: 'Send to Phone',
    alertLangLabel: 'Language',
    messageSentSuccess: 'Message sent successfully!',

    // ── Decision Support extended ─────────────────────────────────────────────
    decisionSupportSubtitle: 'Decision Support System — Pune Municipal Corporation',
    allFilter: 'All',
    immediateFilter: 'Immediate',
    next6hFilter: 'Next 6h',
    next24hFilter: 'Next 24h',
    advisoryFilter: 'Advisory',
    refreshPlan: 'Refresh Plan',
    loadingLabel: 'Loading...',
    next6hBadge: 'NEXT 6H',
    next24hBadge: 'NEXT 24H',

    // ── Trend / status labels ──────────────────────────────────────────────────
    trendStable: '→ stable',
    trendRising: 'rising',
    trendFalling: 'falling',
    forecastListTitle: '48h Forecasts',
    peakAtLabel: 'Peak:',
    atLabel: 'at',
    noneDetected: 'None detected',
    noneHazardLabel: 'NONE',
    riskSuffix: 'Risk',
    riskCatLow: 'Low',
    riskCatModerate: 'Moderate',
    riskCatHigh: 'High',
    riskCatCritical: 'Critical',

    // ── Classification results ──────────────────────────────────────────────────
    classTruePos: 'true positive',
    classFalsePos: 'false positive',
    classTrueNeg: 'true negative',
    classFalseNeg: 'false negative',

    // ── Alert / channel / category labels ──────────────────────────────────────
    smsMsgLabel: '📱 SMS Message',
    whatsappMsgLabel: '💬 WhatsApp Message',
    nearestShelterLabel: '🏩 Nearest Shelter:',
    channelSms: 'SMS',
    channelWhatsapp: 'WHATSAPP',

    // ── New keys — App toasts ──────────────────────────────────────────────
    fetchError: 'Failed to fetch data from server',
    dataRefreshed: 'Data refreshed',
    ingestionStarting: 'Starting weather data ingestion…',
    ingestionComplete: 'Ingestion complete',
    ingestionFailed: 'Ingestion failed',
    calculatingRisks: 'Calculating risk scores…',
    risksCalculated: 'Calculated risks',
    riskCalcFailed: 'Risk calculation failed',

    // ── New keys — Resource names ─────────────────────────────────────────
    resPumps: 'Pumps',
    resBuses: 'Buses',
    resCamps: 'Relief Camps',
    resCooling: 'Cooling Centers',
    resMedical: 'Medical Units',
    optimizeSuccess: 'Optimization complete!',
    optimizeFailed: 'Optimization failed',
    optimizeError: 'Error running optimization',
    coverageLabel: 'coverage',
    topWardsNeeding: 'Top wards needing more',
    unitsNeeded: 'needed',

    // ── New keys — Scenario ───────────────────────────────────────────────
    scenarioParams: 'Scenario Parameters',
    rainfallMultiplier: 'Rainfall Multiplier',
    tempAnomaly: 'Temperature Anomaly',
    drainageEfficiency: 'Drainage Efficiency',
    populationGrowthLabel: 'Population Growth',
    runScenario: 'Run Scenario Simulation',
    resetLabel: 'Reset',
    scenarioSuccess: 'Scenario simulation complete!',
    scenarioFailed: 'Scenario simulation failed',
    scenarioError: 'Error running scenario',
    highImpactDesc: 'This scenario shows significant risk increases. Consider pre-positioning resources and activating emergency protocols.',
    presetHeavyMonsoon: 'Heavy Monsoon',
    presetCloudburst: 'Cloudburst',
    presetHeatwave: 'Severe Heatwave',
    presetCompound: 'Compound Crisis',
    presetDrainage: 'Drainage Upgrade',
    presetHeavyMonsoonDesc: 'Simulate 2.5× monsoon rainfall',
    presetCloudburstDesc: 'Extreme rain + reduced drainage',
    presetHeatwaveDesc: '+6°C temperature anomaly',
    presetCompoundDesc: 'Rain + heat + infra stress',
    presetDrainageDesc: '40% drainage improvement',
    sliderDrought: 'Drought',
    sliderNormal: 'Normal',
    sliderExtreme: 'Extreme',
    sliderHeatwave: 'Heatwave',
    sliderBlocked: 'Blocked',
    sliderImproved: 'Improved',
    sliderCurrent: 'Current',
    sliderGrowth: 'Growth',
    sliderRapid: 'Rapid',
    scenarioDescNeutral: 'All parameters at baseline — adjust sliders or pick a preset to simulate a scenario.',
    scenarioDescRainfall: 'rainfall intensity',
    scenarioDescReducedRain: 'reduced rainfall',
    scenarioDescTempRise: 'temperature rise',
    scenarioDescDegradedDrain: 'degraded drainage',
    scenarioDescImprovedDrain: 'improved drainage',
    scenarioDescPopGrowth: 'population growth',
    scenarioDescSimulating: 'Simulating:',

    // ── New keys — Historical Validation ──────────────────────────────────
    histValidTitle: 'Historical Event Validation',
    histValidDesc: 'Validate our risk model against real documented Pune disaster events using actual archived weather data',
    wardsAffected: 'wards affected',
    rainfallMm: 'mm rainfall',
    validationProgress: 'Fetching archived weather from Open-Meteo → running risk model',
    modelPrediction: 'Model Prediction',
    severityCatastrophic: 'CATASTROPHIC',
    severitySevere: 'SEVERE',
    severityModerate: 'MODERATE',

    // ── New keys — Decision Support ───────────────────────────────────────
    catDeploy: 'DEPLOY',
    catEvacuate: 'EVACUATE',
    catAlert: 'ALERT',
    catMonitor: 'MONITOR',
    catPrepare: 'PREPARE',
    assignedLabel: 'Assigned:',
    acknowledgeBtn: 'Acknowledge',
    acknowledgedLabel: 'Acknowledged',
    deployBtn: 'Deploy',

    // ── New keys — Misc ────────────────────────────────────────────────────
    clickCalculate: 'Click "Calculate" to generate risk scores',
    facilitiesLabel: 'Facilities',
    capLabel: 'Cap',
    shelterLabel: 'Shelter',
    walkLabel: 'Walk',
    forWards: 'wards',
  },

  hi: {
    // ── App header ──────────────────────────────────────────────────────────
    appName: 'प्रकल्प',
    appSubtitle: 'पूर्वानुमान जोखिम आकलन और ज्ञान विश्लेषण',
    live: 'लाइव',
    updated: 'अपडेट किया गया',
    refresh: 'रिफ्रेश',
    ingest: 'डेटा लें',
    calculate: 'गणना करें',

    // ── Tabs ─────────────────────────────────────────────────────────────────
    tabRiskMap: 'जोखिम मानचित्र',
    tabSummary: 'सारांश',
    tabOptimizer: 'अनुकूलक',
    tabScenarios: 'परिदृश्य',
    tabForecast: 'पूर्वानुमान',
    tabValidation: 'सत्यापन',
    tabAlerts: 'अलर्ट',
    tabEvacuation: 'निकासी',
    tabCommand: 'कमांड',

    // ── Map panel labels ──────────────────────────────────────────────────────
    wardRankings: 'वार्ड रैंकिंग',
    wardDetails: 'वार्ड विवरण',

    // ── Footer ────────────────────────────────────────────────────────────────
    dataSources: 'डेटा स्रोत',
    openMeteo: 'ओपन-मेटियो एपीआई',
    pmcWard: 'पीएमसी वार्ड डेटा',
    census: 'जनगणना 2011',

    // ── Evacuation Map ────────────────────────────────────────────────────────
    evacTitle: 'निकासी मार्ग अनुकूलक',
    evacSubtitle: 'निकटतम आश्रयों तक सुरक्षित मार्ग, बाढ़-प्रवण सड़कों से बचते हुए',
    computeRoutes: 'मार्ग निकालें',
    allRoutes: 'सभी मार्ग',
    floodSim: 'बाढ़ सिम',
    sos: 'SOS',
    emergencyBroadcast: 'आपातकालीन प्रसारण सक्रिय',
    elapsed: 'बीता समय',
    peopleEvacuating: 'निकासी में लोग',
    highRiskWards: 'उच्च जोखिम वाले वार्ड',
    endBroadcast: 'प्रसारण बंद करें',
    totalWards: 'कुल वार्ड',
    shelters: 'आश्रय',
    immediate: 'तत्काल',
    avgWalk: 'औसत चलने का समय',
    wardRoutes: 'वार्ड मार्ग',
    recommendedShelter: 'अनुशंसित आश्रय',
    alternativeShelters: 'वैकल्पिक आश्रय',
    allShelters: 'सभी आश्रय',
    distance: 'दूरी',
    walking: 'पैदल',
    routeSafety: 'मार्ग सुरक्षा',
    capacity: 'क्षमता',
    walkingEta: 'पैदल अनुमानित समय',
    estimatedFillRate: 'अनु. भरने की दर',
    avoidFloodProne: 'बचें (बाढ़-प्रवण)',
    useInstead: 'इसे उपयोग करें',
    clickWard: 'निकासी मार्ग देखने के लिए नक्शे या सूची से कोई वार्ड चुनें',
    routesAnimateRealtime: 'मार्ग वास्तविक समय में मानचित्र पर दिखाए जाते हैं',
    evacuateNow: 'अभी निकलें',
    prepare: 'तैयार रहें',
    monitor: 'निगरानी करें',
    standby: 'स्टैंडबाय',
    safe: 'सुरक्षित',
    moderateRiskStatus: 'मध्यम जोखिम',
    unsafeStatus: 'असुरक्षित',
    type: 'प्रकार',
    riskLevel: 'जोखिम स्तर',

    // ── Legend ────────────────────────────────────────────────────────────────
    legend: 'संकेत',
    highRiskWard: 'उच्च जोखिम वार्ड',
    mediumRisk: 'मध्यम जोखिम',
    lowRisk: 'कम जोखिम',
    recShelter: 'अनुशंसित आश्रय',
    altShelter: 'वैकल्पिक आश्रय',
    otherShelter: 'अन्य आश्रय',
    activeRoute: 'सक्रिय मार्ग',
    otherRoutes: 'अन्य मार्ग',

    // ── Risk Summary ──────────────────────────────────────────────────────────
    noRiskData: 'जोखिम डेटा उपलब्ध नहीं है',
    cityRiskSummary: 'शहर जोखिम सारांश',
    puneMunicipal: 'पुणे महानगरपालिका',
    overallStatus: 'कुल स्थिति',
    totalPopulation: 'कुल जनसंख्या',
    criticalWards: 'गंभीर वार्ड',
    highRiskWardsLabel: 'उच्च जोखिम वार्ड',
    riskDistribution: 'जोखिम वितरण',
    avgRiskByHazard: 'खतरे के अनुसार औसत जोखिम',
    floodRisk: 'बाढ़ जोखिम',
    heatRisk: 'गर्मी जोखिम',
    top10Wards: 'शीर्ष 10 सर्वाधिक जोखिम वार्ड',
    rank: 'रैंक',
    ward: 'वार्ड',
    topHazard: 'मुख्य खतरा',
    riskScore: 'जोखिम स्कोर',
    population: 'जनसंख्या',
    statusNormal: 'सामान्य',
    statusHigh: 'उच्च',
    statusCritical: 'गंभीर',

    // ── Resource Optimizer ────────────────────────────────────────────────────
    resourceConfig: 'संसाधन कॉन्फ़िगरेशन',
    prioritizeSurging: 'बढ़ते वार्डों को प्राथमिकता दें',
    prioritizeSurgingOn: 'चालू — तेजी से बढ़ते जोखिम वाले वार्डों को अतिरिक्त महत्व',
    prioritizeSurgingOff: 'बंद — केवल वर्तमान जोखिम × जनसंख्या के अनुसार',
    runOptimization: 'अनुकूलन चलाएँ',
    noDeployRequired: 'तैनाती आवश्यक नहीं',
    noDeployDesc: 'सभी वार्ड जोखिम स्कोर सीमा से नीचे हैं',
    highestNeed: 'सर्वाधिक आवश्यकता',
    deployed: 'तैनात',
    unitsAllocated: 'इकाइयाँ आवंटित',
    allocationSummary: 'संसाधन प्रकार के अनुसार आवंटन सारांश',
    allocated: 'आवंटित',
    resourceGapAnalysis: 'संसाधन अंतर विश्लेषण',
    overallCoverage: 'कुल कवरेज',
    totalNeeded: 'कुल आवश्यक',
    totalAvailable: 'कुल उपलब्ध',
    deficit: 'कमी',
    available: 'उपलब्ध',
    required: 'आवश्यक',
    sufficient: 'पर्याप्त',
    wardwiseAllocations: 'वार्ड-वार आवंटन',
    allocationRationale: 'आवंटन तर्क',
    needScore: 'आवश्यकता स्कोर',

    // ── Scenario Simulator ────────────────────────────────────────────────────
    quickPresets: 'त्वरित प्रीसेट',
    baseline: 'आधार रेखा',
    scenario: 'परिदृश्य',
    floodRiskChange: 'बाढ़ जोखिम परिवर्तन',
    heatRiskChange: 'गर्मी जोखिम परिवर्तन',
    highImpactScenario: 'उच्च प्रभाव परिदृश्य',
    newlyCriticalWards: 'नए गंभीर वार्ड',
    noChange: 'कोई बदलाव नहीं',
    riskChangeByWard: 'वार्ड अनुसार जोखिम परिवर्तन (शीर्ष 10)',
    detailedWardImpact: 'विस्तृत वार्ड प्रभाव',
    status: 'स्थिति',

    // ── Forecast ─────────────────────────────────────────────────────────────
    riskTimeline: 'जोखिम समयरेखा (48 घंटे)',
    selectWardForecast: 'पूर्वानुमान देखने के लिए वार्ड चुनें',
    totalWardsLabel: 'कुल वार्ड',
    peakRisk: 'अधिकतम जोखिम',
    dangerWindow: 'खतरा अवधि',
    reachingCritical: 'गंभीर स्तर पर पहुँचना',
    riskRising: 'जोखिम बढ़ रहा है',
    hourlyDetail: 'प्रति घंटा विवरण',

    // ── Historical Validation ─────────────────────────────────────────────────
    selectHistoricalEvent: 'सत्यापन के लिए ऐतिहासिक घटना चुनें',
    modelTestedDesc: 'मॉडल को उस घटना के वास्तविक मौसम डेटा से परखा जाएगा',
    runningValidation: 'ऐतिहासिक डेटा के विरुद्ध सत्यापन चल रहा है...',
    accuracy: 'सटीकता',
    precision: 'परिशुद्धता',
    recall: 'रिकॉल',
    leadTime: 'अग्रिम समय',
    predicted: 'अनुमानित',
    actuallyHit: 'वास्तव में प्रभावित',
    result: 'परिणाम',
    correctlyFlagged: 'सही ढंग से जोखिम में चिह्नित',
    wardLevelPredictions: 'वार्ड स्तरीय भविष्यवाणी बनाम वास्तविक',

    // ── Alerts ────────────────────────────────────────────────────────────────
    alertsSubtitle: 'नागरिकों और अधिकारियों के लिए रीयल-टाइम द्विभाषी अलर्ट',
    recommendedActions: 'अनुशंसित कार्रवाइयाँ:',

    // ── Risk Map ─────────────────────────────────────────────────────────────
    wardId: 'वार्ड ID:',
    riskScoreLabel: 'जोखिम स्कोर:',
    topHazardLabel: 'मुख्य खतरा:',
    floodLabel: 'बाढ़:',
    heatLabel: 'गर्मी:',
    populationLabel: 'जनसंख्या:',
    openStreetMap: 'OpenStreetMap',

    // ── Ward Detail ───────────────────────────────────────────────────────────
    selectWardDetail: 'विवरण देखने के लिए वार्ड चुनें',
    clickWardHint: 'सूची या नक्शे में वार्ड पर क्लिक करें',
    recommendations: 'सिफारिशें',
    eventCurrent: 'घटना (वर्तमान)',
    baselineLabel: 'आधार रेखा',
    areaLabel: 'क्षेत्र:',
    densityLabel: 'घनत्व:',
    elevLabel: 'ऊँचाई:',
    popLabel: 'जनसंख्या:',

    // ── Decision Support ─────────────────────────────────────────────────────
    commandCenter: 'कमांड सेंटर',
    situationLevel: 'स्थिति स्तर',
    populationAtRisk: 'जोखिम में जनसंख्या',
    readiness: 'तत्परता',
    totalActions: 'कुल कार्रवाइयाँ',
    criticalPending: 'गंभीर लंबित',
    allClear: 'सब ठीक',
    noActionsRequired: 'वर्तमान जोखिम स्तरों पर कोई कार्रवाई आवश्यक नहीं',
    impact: 'प्रभाव:',
    why: 'क्यों:',

    // ── Risk Level Labels ─────────────────────────────────────────────────────
    low030: 'कम (0-30%)',
    moderate3160: 'मध्यम (31-60%)',
    high6180: 'उच्च (61-80%)',
    critical81100: 'अत्यंत जोखिम (81-100%)',

    // ── Ward Detail extended ──────────────────────────────────────────────────
    riskComparison: 'जोखिम तुलना',
    vsBaseline: 'आधाररेखा से तुलना',
    aboveBaseline: 'आधाररेखा से उपर',
    belowBaseline: 'आधाररेखा से नीचे',
    riskExplanation: 'जोखिम स्पष्टीकरण',
    topContribFactors: 'मुख्य योगदान कारक',
    floodBtn: 'बाढ़',
    heatBtn: 'गर्मी',

    // ── Resource Optimizer extended ───────────────────────────────────────────
    highestRecordedRisk: 'सर्वाधिक दर्ज जोखिम:',
    noDeployUntilDeter: 'जोखिम स्थिति बिगड़ने तक कोई संसाधन तैनात नहीं किया जाएगा।',

    // ── Scenario extended ─────────────────────────────────────────────────────
    floodDeltaHeader: 'बाढ़ Δ',
    heatDeltaHeader: 'गर्मी Δ',
    statusIncreased: 'बढ़ा',
    statusReduced: 'घटा',
    statusHighImpact: 'उच्च प्रभाव',
    statusNewCritical: 'नया गंभीर',

    // ── Forecast extended ─────────────────────────────────────────────────────
    criticalLine: 'अत्यंत जोखिम',
    highLine: 'उच्च',
    floodRiskName: 'बाढ़ जोखिम',
    heatRiskName: 'गर्मी जोखिम',
    criticalInHours: 'गंभीर स्थिति में',
    populationStat: 'जनसंख्या',
    baselineFloodStat: 'आधार बाढ़',
    baselineHeatStat: 'आधार गर्मी',

    // ── Historical Validation extended ────────────────────────────────────────
    modelWouldPredict: 'मॉडल ने भविष्यवाणी की होती',
    modelMayMiss: 'मॉडल चूक सकता था',
    avgRiskForWards: 'प्रभावित वार्डों के लिए औसत जोखिम',
    leadTimeStat: 'अग्रिम समय',
    hoursBeforeEvent: 'घंटे पहले',
    truePosTitle: 'सही सकारात्मक',
    falseNegTitle: 'गलत नकारात्मक',
    missedActually: 'छूटे — वास्तव में प्रभावित',
    wardByWardAnalysis: 'वार्ड-दर-वार्ड विश्लेषण',
    yesLabel: 'हाँ',

    // ── Alerts extended ───────────────────────────────────────────────────────
    alertPanelTitle: 'अलर्ट सिस्टम — SMS / WhatsApp एकीकरण',
    generateAlerts: 'अलर्ट बनाएँ',
    citizenAlertsLabel: 'नागरिक अलर्ट',
    authorityAlertsLabel: 'प्राधिकरण / PMC अलर्ट',
    noAuthorityAlerts: 'वर्तमान जोखिम स्तरों पर कोई प्राधिकरण-स्तरीय अलर्ट नहीं',
    alertTotal: 'कुल',
    alertEmergency: 'आपातकाल',
    alertWarning: 'चेतावनी',
    alertWatch: 'निगरानी',
    alertAdvisory: 'सलाह',
    sendToPhone: 'फ़ोन पर भेजें',
    alertLangLabel: 'भाषा',
    messageSentSuccess: 'संदेश सफलतापूर्वक भेजा गया!',

    // ── Decision Support extended ─────────────────────────────────────────────
    decisionSupportSubtitle: 'निर्णय समर्थन प्रणाली — पुणे महानगरपालिका',
    allFilter: 'सभी',
    immediateFilter: 'तत्काल',
    next6hFilter: 'अगले 6 घंटे',
    next24hFilter: 'अगले 24 घंटे',
    advisoryFilter: 'सलाह',
    refreshPlan: 'योजना ताज़ा करें',
    loadingLabel: 'लोड हो रहा है...',
    next6hBadge: 'अगले 6H',
    next24hBadge: 'अगले 24H',

    // ── Trend / status labels ──────────────────────────────────────────────────
    trendStable: '→ स्थिर',
    trendRising: 'बढ़ रहा',
    trendFalling: 'घट रहा',
    forecastListTitle: '48 घंटे पूर्वानुमान',
    peakAtLabel: 'चरम:',
    atLabel: 'पर',
    noneDetected: 'कोई नहीं मिला',
    noneHazardLabel: 'कोई नहीं',
    riskSuffix: 'जोखिम',
    riskCatLow: 'कम',
    riskCatModerate: 'मध्यम',
    riskCatHigh: 'उच्च',
    riskCatCritical: 'गंभीर',

    // ── Classification results ──────────────────────────────────────────────────
    classTruePos: 'सही सकारात्मक',
    classFalsePos: 'गलत सकारात्मक',
    classTrueNeg: 'सही नकारात्मक',
    classFalseNeg: 'गलत नकारात्मक',

    // ── Alert / channel / category labels ──────────────────────────────────────
    smsMsgLabel: '📱 SMS संदेश',
    whatsappMsgLabel: '💬 WhatsApp संदेश',
    nearestShelterLabel: '🏩 नजदीकी आश्रय:',
    channelSms: 'SMS',
    channelWhatsapp: 'WHATSAPP',

    // ── New keys — App toasts ──────────────────────────────────────────────
    fetchError: 'सर्वर से डेटा प्राप्त करने में विफल',
    dataRefreshed: 'डेटा रिफ्रेश हो गया',
    ingestionStarting: 'मौसम डेटा इंजेशन शुरू हो रहा है…',
    ingestionComplete: 'इंजेशन पूर्ण',
    ingestionFailed: 'इंजेशन विफल',
    calculatingRisks: 'जोखिम स्कोर गणना हो रही है…',
    risksCalculated: 'जोखिम गणना पूर्ण',
    riskCalcFailed: 'जोखिम गणना विफल',

    // ── New keys — Resource names ─────────────────────────────────────────
    resPumps: 'पंप',
    resBuses: 'बसें',
    resCamps: 'राहत शिविर',
    resCooling: 'शीतलन केंद्र',
    resMedical: 'चिकित्सा इकाइयाँ',
    optimizeSuccess: 'अनुकूलन पूर्ण!',
    optimizeFailed: 'अनुकूलन विफल',
    optimizeError: 'अनुकूलन चलाने में त्रुटि',
    coverageLabel: 'कवरेज',
    topWardsNeeding: 'शीर्ष वार्ड जिन्हें अधिक चाहिए',
    unitsNeeded: 'आवश्यक',

    // ── New keys — Scenario ───────────────────────────────────────────────
    scenarioParams: 'परिदृश्य पैरामीटर',
    rainfallMultiplier: 'वर्षा गुणक',
    tempAnomaly: 'तापमान विसंगति',
    drainageEfficiency: 'जल निकासी दक्षता',
    populationGrowthLabel: 'जनसंख्या वृद्धि',
    runScenario: 'परिदृश्य सिमुलेशन चलाएँ',
    resetLabel: 'रीसेट',
    scenarioSuccess: 'परिदृश्य सिमुलेशन पूर्ण!',
    scenarioFailed: 'परिदृश्य सिमुलेशन विफल',
    scenarioError: 'परिदृश्य चलाने में त्रुटि',
    highImpactDesc: 'यह परिदृश्य महत्वपूर्ण जोखिम वृद्धि दर्शाता है। संसाधन पूर्व-स्थापन और आपातकालीन प्रोटोकॉल सक्रिय करने पर विचार करें।',
    presetHeavyMonsoon: 'भारी मानसून',
    presetCloudburst: 'बादल फटना',
    presetHeatwave: 'तीव्र लू',
    presetCompound: 'जटिल संकट',
    presetDrainage: 'जल निकासी सुधार',
    presetHeavyMonsoonDesc: '2.5× मानसून वर्षा सिमुलेशन',
    presetCloudburstDesc: 'अत्यधिक वर्षा + कम जल निकासी',
    presetHeatwaveDesc: '+6°C तापमान विसंगति',
    presetCompoundDesc: 'वर्षा + गर्मी + अवसंरचना तनाव',
    presetDrainageDesc: '40% जल निकासी सुधार',
    sliderDrought: 'सूखा',
    sliderNormal: 'सामान्य',
    sliderExtreme: 'अत्यधिक',
    sliderHeatwave: 'लू',
    sliderBlocked: 'अवरुद्ध',
    sliderImproved: 'सुधारित',
    sliderCurrent: 'वर्तमान',
    sliderGrowth: 'वृद्धि',
    sliderRapid: 'तीव्र',
    scenarioDescNeutral: 'सभी पैरामीटर आधाररेखा पर — परिदृश्य सिमुलेट करने के लिए स्लाइडर समायोजित करें या प्रीसेट चुनें।',
    scenarioDescRainfall: 'वर्षा तीव्रता',
    scenarioDescReducedRain: 'कम वर्षा',
    scenarioDescTempRise: 'तापमान वृद्धि',
    scenarioDescDegradedDrain: 'खराब जल निकासी',
    scenarioDescImprovedDrain: 'सुधारित जल निकासी',
    scenarioDescPopGrowth: 'जनसंख्या वृद्धि',
    scenarioDescSimulating: 'सिमुलेट हो रहा है:',

    // ── New keys — Historical Validation ──────────────────────────────────
    histValidTitle: 'ऐतिहासिक घटना सत्यापन',
    histValidDesc: 'वास्तविक मौसम डेटा का उपयोग करते हुए वास्तविक दस्तावेज़ी पुणे आपदा घटनाओं से हमारे जोखिम मॉडल का सत्यापन करें',
    wardsAffected: 'वार्ड प्रभावित',
    rainfallMm: 'मिमी वर्षा',
    validationProgress: 'ओपन-मेटियो से संग्रहीत मौसम लाया जा रहा है → जोखिम मॉडल चलाया जा रहा है',
    modelPrediction: 'मॉडल अनुमान',
    severityCatastrophic: 'विनाशकारी',
    severitySevere: 'गंभीर',
    severityModerate: 'मध्यम',

    // ── New keys — Decision Support ───────────────────────────────────────
    catDeploy: 'तैनात',
    catEvacuate: 'निकासी',
    catAlert: 'सतर्कता',
    catMonitor: 'निगरानी',
    catPrepare: 'तैयारी',
    assignedLabel: 'नियुक्त:',
    acknowledgeBtn: 'स्वीकार करें',
    acknowledgedLabel: 'स्वीकार किया',
    deployBtn: 'तैनात करें',

    // ── New keys — Misc ──────────────────────────────────────────────────
    clickCalculate: '"गणना करें" पर क्लिक करके जोखिम स्कोर बनाएँ',
    facilitiesLabel: 'सुविधाएँ',
    capLabel: 'क्षमता',
    riskLabel: 'जोखिम',
    shelterLabel: 'आश्रय',
    walkLabel: 'पैदल',
    forWards: 'वार्ड',
  },

  mr: {
    // ── App header ──────────────────────────────────────────────────────────
    appName: 'प्रकल्प',
    appSubtitle: 'अंदाजपत्रक जोखिम मूल्यांकन आणि ज्ञान विश्लेषण',
    live: 'थेट',
    updated: 'अद्यतनित',
    refresh: 'रिफ्रेश',
    ingest: 'डेटा घ्या',
    calculate: 'गणना करा',

    // ── Tabs ─────────────────────────────────────────────────────────────────
    tabRiskMap: 'जोखीम नकाशा',
    tabSummary: 'सारांश',
    tabOptimizer: 'ऑप्टिमायझर',
    tabScenarios: 'परिस्थिती',
    tabForecast: 'अंदाज',
    tabValidation: 'प्रमाणीकरण',
    tabAlerts: 'सूचना',
    tabEvacuation: 'स्थलांतर',
    tabCommand: 'कमांड',

    // ── Map panel labels ──────────────────────────────────────────────────────
    wardRankings: 'वार्ड क्रमवारी',
    wardDetails: 'वार्ड तपशील',

    // ── Footer ────────────────────────────────────────────────────────────────
    dataSources: 'डेटा स्रोत',
    openMeteo: 'ओपन-मेटियो API',
    pmcWard: 'PMC वार्ड डेटा',
    census: 'जनगणना 2011',

    // ── Evacuation Map ────────────────────────────────────────────────────────
    evacTitle: 'स्थलांतर मार्ग ऑप्टिमायझर',
    evacSubtitle: 'जवळच्या निवाऱ्यांकडे सुरक्षित मार्ग, पूर-प्रवण रस्ते टाळत',
    computeRoutes: 'मार्ग काढा',
    allRoutes: 'सर्व मार्ग',
    floodSim: 'पूर सिम',
    sos: 'SOS',
    emergencyBroadcast: 'आपत्कालीन प्रसारण सुरू',
    elapsed: 'उलटलेला वेळ',
    peopleEvacuating: 'स्थलांतरित लोक',
    highRiskWards: 'उच्च जोखीम वार्ड',
    endBroadcast: 'प्रसारण थांबवा',
    totalWards: 'एकूण वार्ड',
    shelters: 'निवारे',
    immediate: 'तात्काळ',
    avgWalk: 'सरासरी चालण्याचा वेळ',
    wardRoutes: 'वार्ड मार्ग',
    recommendedShelter: 'शिफारस केलेला निवारा',
    alternativeShelters: 'पर्यायी निवारे',
    allShelters: 'सर्व निवारे',
    distance: 'अंतर',
    walking: 'पायी',
    routeSafety: 'मार्ग सुरक्षितता',
    capacity: 'क्षमता',
    walkingEta: 'पायी अंदाजित वेळ',
    estimatedFillRate: 'अंदाजे भरण्याचा दर',
    avoidFloodProne: 'टाळा (पूर-प्रवण)',
    useInstead: 'हे वापरा',
    clickWard: 'स्थलांतर मार्ग पाहण्यासाठी नकाशावर किंवा यादीत वार्ड निवडा',
    routesAnimateRealtime: 'मार्ग नकाशावर रिअल-टाइममध्ये दाखवले जातात',
    evacuateNow: 'आत्ता निघा',
    prepare: 'तयार राहा',
    monitor: 'लक्ष ठेवा',
    standby: 'स्टँडबाय',
    safe: 'सुरक्षित',
    moderateRiskStatus: 'मध्यम जोखीम',
    unsafeStatus: 'असुरक्षित',
    type: 'प्रकार',
    riskLevel: 'जोखीम पातळी',

    // ── Legend ────────────────────────────────────────────────────────────────
    legend: 'चिन्हे',
    highRiskWard: 'उच्च जोखीम वार्ड',
    mediumRisk: 'मध्यम जोखीम',
    lowRisk: 'कमी जोखीम',
    recShelter: 'शिफारस निवारा',
    altShelter: 'पर्यायी निवारा',
    otherShelter: 'इतर निवारा',
    activeRoute: 'सक्रिय मार्ग',
    otherRoutes: 'इतर मार्ग',

    // ── Risk Summary ──────────────────────────────────────────────────────────
    noRiskData: 'जोखीम डेटा उपलब्ध नाही',
    cityRiskSummary: 'शहर जोखीम सारांश',
    puneMunicipal: 'पुणे महानगरपालिका',
    overallStatus: 'एकूण स्थिती',
    totalPopulation: 'एकूण लोकसंख्या',
    criticalWards: 'गंभीर वार्ड',
    highRiskWardsLabel: 'उच्च जोखीम वार्ड',
    riskDistribution: 'जोखीम वितरण',
    avgRiskByHazard: 'धोक्यानुसार सरासरी जोखीम',
    floodRisk: 'पूर जोखीम',
    heatRisk: 'उष्णता जोखीम',
    top10Wards: 'शीर्ष 10 सर्वाधिक जोखीम वार्ड',
    rank: 'क्रमांक',
    ward: 'वार्ड',
    topHazard: 'मुख्य धोका',
    riskScore: 'जोखीम गुण',
    population: 'लोकसंख्या',
    statusNormal: 'सामान्य',
    statusHigh: 'उच्च',
    statusCritical: 'गंभीर',

    // ── Resource Optimizer ────────────────────────────────────────────────────
    resourceConfig: 'संसाधन कॉन्फिगरेशन',
    prioritizeSurging: 'वाढत्या वार्डांना प्राधान्य द्या',
    prioritizeSurgingOn: 'चालू — वेगाने वाढणाऱ्या जोखीम वार्डांना अतिरिक्त महत्त्व',
    prioritizeSurgingOff: 'बंद — फक्त सध्याची जोखीम × लोकसंख्येनुसार',
    runOptimization: 'ऑप्टिमायझेशन चालवा',
    noDeployRequired: 'तैनाती आवश्यक नाही',
    noDeployDesc: 'सर्व वार्ड जोखीम गुण उंबरठ्याखाली आहेत',
    highestNeed: 'सर्वाधिक गरज',
    deployed: 'तैनात',
    unitsAllocated: 'युनिट वाटप',
    allocationSummary: 'संसाधन प्रकारानुसार वाटप सारांश',
    allocated: 'वाटप',
    resourceGapAnalysis: 'संसाधन तूट विश्लेषण',
    overallCoverage: 'एकूण कव्हरेज',
    totalNeeded: 'एकूण आवश्यक',
    totalAvailable: 'एकूण उपलब्ध',
    deficit: 'तूट',
    available: 'उपलब्ध',
    required: 'आवश्यक',
    sufficient: 'पुरेसे',
    wardwiseAllocations: 'वार्डनिहाय वाटप',
    allocationRationale: 'वाटप कारण',
    needScore: 'गरज गुण',

    // ── Scenario Simulator ────────────────────────────────────────────────────
    quickPresets: 'त्वरित प्रीसेट',
    baseline: 'आधाररेषा',
    scenario: 'परिस्थिती',
    floodRiskChange: 'पूर जोखीम बदल',
    heatRiskChange: 'उष्णता जोखीम बदल',
    highImpactScenario: 'उच्च प्रभाव परिस्थिती',
    newlyCriticalWards: 'नवीन गंभीर वार्ड',
    noChange: 'बदल नाही',
    riskChangeByWard: 'वार्डनिहाय जोखीम बदल (शीर्ष 10)',
    detailedWardImpact: 'सविस्तर वार्ड प्रभाव',
    status: 'स्थिती',

    // ── Forecast ─────────────────────────────────────────────────────────────
    riskTimeline: 'जोखीम कालरेषा (48 तास)',
    selectWardForecast: 'अंदाज पाहण्यासाठी वार्ड निवडा',
    totalWardsLabel: 'एकूण वार्ड',
    peakRisk: 'कमाल जोखीम',
    dangerWindow: 'धोक्याचा कालावधी',
    reachingCritical: 'गंभीर पातळीला पोहोचणे',
    riskRising: 'जोखीम वाढत आहे',
    hourlyDetail: 'तासावार तपशील',

    // ── Historical Validation ─────────────────────────────────────────────────
    selectHistoricalEvent: 'प्रमाणीकरणासाठी ऐतिहासिक घटना निवडा',
    modelTestedDesc: 'मॉडेलची त्या घटनेच्या हवामान डेटाशी चाचणी केली जाईल',
    runningValidation: 'ऐतिहासिक डेटाशी प्रमाणीकरण सुरू...',
    accuracy: 'अचूकता',
    precision: 'परिशुद्धता',
    recall: 'रिकॉल',
    leadTime: 'आगाऊ वेळ',
    predicted: 'अंदाजित',
    actuallyHit: 'प्रत्यक्षात बाधित',
    result: 'निकाल',
    correctlyFlagged: 'योग्यरित्या जोखीम म्हणून चिन्हांकित',
    wardLevelPredictions: 'वार्ड पातळी अंदाज विरुद्ध प्रत्यक्ष',

    // ── Alerts ────────────────────────────────────────────────────────────────
    alertsSubtitle: 'नागरिक आणि अधिकाऱ्यांसाठी रिअल-टाइम द्विभाषी सूचना',
    recommendedActions: 'शिफारस केलेल्या कृती:',

    // ── Risk Map ─────────────────────────────────────────────────────────────
    wardId: 'वार्ड ID:',
    riskScoreLabel: 'जोखीम गुण:',
    topHazardLabel: 'मुख्य धोका:',
    floodLabel: 'पूर:',
    heatLabel: 'उष्णता:',
    populationLabel: 'लोकसंख्या:',
    openStreetMap: 'OpenStreetMap',

    // ── Ward Detail ───────────────────────────────────────────────────────────
    selectWardDetail: 'तपशील पाहण्यासाठी वार्ड निवडा',
    clickWardHint: 'यादी किंवा नकाशावर वार्डवर क्लिक करा',
    recommendations: 'शिफारसी',
    eventCurrent: 'घटना (सध्या)',
    baselineLabel: 'आधाररेषा',
    areaLabel: 'क्षेत्र:',
    densityLabel: 'घनता:',
    elevLabel: 'उंची:',
    popLabel: 'लोकसंख्या:',

    // ── Decision Support ─────────────────────────────────────────────────────
    commandCenter: 'कमांड सेंटर',
    situationLevel: 'परिस्थिती पातळी',
    populationAtRisk: 'जोखीमग्रस्त लोकसंख्या',
    readiness: 'सज्जता',
    totalActions: 'एकूण कृती',
    criticalPending: 'गंभीर प्रलंबित',
    allClear: 'सर्व ठीक',
    noActionsRequired: 'सध्याच्या जोखीम पातळीवर कोणतीही कृती आवश्यक नाही',
    impact: 'प्रभाव:',
    why: 'का:',

    // ── Risk Level Labels ─────────────────────────────────────────────────────
    low030: 'कमी (0-30%)',
    moderate3160: 'मध्यम (31-60%)',
    high6180: 'उच्च (61-80%)',
    critical81100: 'अत्यंत जोखीम (81-100%)',

    // ── Ward Detail extended ──────────────────────────────────────────────────
    riskComparison: 'जोखीम तुलना',
    vsBaseline: 'आधाररेषेशी तुलना',
    aboveBaseline: 'आधाररेषेवर',
    belowBaseline: 'आधाररेषेखाली',
    riskExplanation: 'जोखीम स्पष्टीकरण',
    topContribFactors: 'मुख्य कारणीभूत घटक',
    floodBtn: 'पूर',
    heatBtn: 'उष्णता',

    // ── Resource Optimizer extended ───────────────────────────────────────────
    highestRecordedRisk: 'सर्वाधिक नोंदवलेली जोखीम:',
    noDeployUntilDeter: 'जोखीम परिस्थिती बिघडेपर्यंत कोणतेही संसाधन तैनात केले जाणार नाहीत.',

    // ── Scenario extended ─────────────────────────────────────────────────────
    floodDeltaHeader: 'पूर Δ',
    heatDeltaHeader: 'उष्णता Δ',
    statusIncreased: 'वाढले',
    statusReduced: 'कमी झाले',
    statusHighImpact: 'उच्च प्रभाव',
    statusNewCritical: 'नवीन गंभीर',

    // ── Forecast extended ─────────────────────────────────────────────────────
    criticalLine: 'अत्यंत धोकादायक',
    highLine: 'उच्च',
    floodRiskName: 'पूर जोखीम',
    heatRiskName: 'उष्णता जोखीम',
    criticalInHours: 'गंभीर स्थितीत',
    populationStat: 'लोकसंख्या',
    baselineFloodStat: 'आधाररेषा पूर',
    baselineHeatStat: 'आधाररेषा उष्णता',

    // ── Historical Validation extended ────────────────────────────────────────
    modelWouldPredict: 'मॉडेलने अंदाज केला असता',
    modelMayMiss: 'मॉडेल चुकले असते',
    avgRiskForWards: 'प्रभावित वार्डांसाठी सरासरी जोखीम',
    leadTimeStat: 'आगाउ वेळ',
    hoursBeforeEvent: 'तास आधी',
    truePosTitle: 'सत्य सकारात्मक',
    falseNegTitle: 'चुकीचे नकारात्मक',
    missedActually: 'चुकवले — प्रत्यक्षात बाधित',
    wardByWardAnalysis: 'वार्ड-दर-वार्ड विश्लेषण',
    yesLabel: 'होय',

    // ── Alerts extended ───────────────────────────────────────────────────────
    alertPanelTitle: 'सूचना प्रणाली — SMS / WhatsApp एकत्रीकरण',
    generateAlerts: 'सूचना तयार करा',
    citizenAlertsLabel: 'नागरिक सूचना',
    authorityAlertsLabel: 'प्राधिकरण / PMC सूचना',
    noAuthorityAlerts: 'सध्याच्या जोखीम पातळीवर कोणत्याही प्राधिकरण-स्तरीय सूचना नाहीत',
    alertTotal: 'एकूण',
    alertEmergency: 'आणीबाणी',
    alertWarning: 'इशारा',
    alertWatch: 'निरीक्षण',
    alertAdvisory: 'सल्ला',
    sendToPhone: 'फोनवर पाठवा',
    alertLangLabel: 'भाषा',
    messageSentSuccess: 'संदेश यशस्वीरित्या पाठवला!',

    // ── Decision Support extended ─────────────────────────────────────────────
    decisionSupportSubtitle: 'निर्णय समर्थन प्रणाली — पुणे महानगरपालिका',
    allFilter: 'सर्व',
    immediateFilter: 'त्वरित',
    next6hFilter: 'पुढील 6 तास',
    next24hFilter: 'पुढील 24 तास',
    advisoryFilter: 'सल्ला',
    refreshPlan: 'योजना ताजी करा',
    loadingLabel: 'लोड होत आहे...',
    next6hBadge: 'पुढील 6H',
    next24hBadge: 'पुढील 24H',

    // ── Trend / status labels ──────────────────────────────────────────────────
    trendStable: '→ स्थिर',
    trendRising: 'वाढत आहे',
    trendFalling: 'कमी होत आहे',
    forecastListTitle: '48 तास अंदाज',
    peakAtLabel: 'कमाल:',
    atLabel: 'वर',
    noneDetected: 'काहीही आढळले नाही',
    noneHazardLabel: 'काही नाही',
    riskSuffix: 'जोखीम',
    riskCatLow: 'कमी',
    riskCatModerate: 'मध्यम',
    riskCatHigh: 'उच्च',
    riskCatCritical: 'गंभीर',

    // ── Classification results ──────────────────────────────────────────────────
    classTruePos: 'खरे सकारात्मक',
    classFalsePos: 'खोटे सकारात्मक',
    classTrueNeg: 'खरे नकारात्मक',
    classFalseNeg: 'खोटे नकारात्मक',

    // ── Alert / channel / category labels ──────────────────────────────────────
    smsMsgLabel: '📱 SMS संदेश',
    whatsappMsgLabel: '💬 WhatsApp संदेश',
    nearestShelterLabel: '🏩 जवळचा निवारा:',
    channelSms: 'SMS',
    channelWhatsapp: 'WHATSAPP',

    // ── New keys — App toasts ──────────────────────────────────────────────
    fetchError: 'सर्व्हरवरून डेटा मिळवण्यात अयशस्वी',
    dataRefreshed: 'डेटा रिफ्रेश झाला',
    ingestionStarting: 'हवामान डेटा इंजेशन सुरू होत आहे…',
    ingestionComplete: 'इंजेशन पूर्ण',
    ingestionFailed: 'इंजेशन अयशस्वी',
    calculatingRisks: 'जोखीम गुण मोजले जात आहेत…',
    risksCalculated: 'जोखीम गणना पूर्ण',
    riskCalcFailed: 'जोखीम गणना अयशस्वी',

    // ── New keys — Resource names ─────────────────────────────────────────
    resPumps: 'पंप',
    resBuses: 'बसेस',
    resCamps: 'मदत शिबिरे',
    resCooling: 'शीतकरण केंद्रे',
    resMedical: 'वैद्यकीय युनिट',
    optimizeSuccess: 'ऑप्टिमायझेशन पूर्ण!',
    optimizeFailed: 'ऑप्टिमायझेशन अयशस्वी',
    optimizeError: 'ऑप्टिमायझेशन चालवताना त्रुटी',
    coverageLabel: 'कव्हरेज',
    topWardsNeeding: 'अधिक गरज असलेले शीर्ष वार्ड',
    unitsNeeded: 'आवश्यक',

    // ── New keys — Scenario ───────────────────────────────────────────────
    scenarioParams: 'परिस्थिती पॅरामीटर',
    rainfallMultiplier: 'पाऊस गुणक',
    tempAnomaly: 'तापमान विसंगती',
    drainageEfficiency: 'निचरा कार्यक्षमता',
    populationGrowthLabel: 'लोकसंख्या वाढ',
    runScenario: 'परिस्थिती सिम्युलेशन चालवा',
    resetLabel: 'रीसेट',
    scenarioSuccess: 'परिस्थिती सिम्युलेशन पूर्ण!',
    scenarioFailed: 'परिस्थिती सिम्युलेशन अयशस्वी',
    scenarioError: 'परिस्थिती चालवताना त्रुटी',
    highImpactDesc: 'या परिस्थितीत जोखमीत लक्षणीय वाढ दिसत आहे. संसाधने पूर्व-तैनात करणे आणि आपत्कालीन प्रोटोकॉल सक्रिय करणे विचारात घ्या.',
    presetHeavyMonsoon: 'जोरदार मान्सून',
    presetCloudburst: 'ढगफुटी',
    presetHeatwave: 'तीव्र उष्णतेची लाट',
    presetCompound: 'संयुक्त संकट',
    presetDrainage: 'निचरा सुधारणा',
    presetHeavyMonsoonDesc: '2.5× मान्सून पाऊस सिम्युलेशन',
    presetCloudburstDesc: 'अत्यंत पाऊस + कमी निचरा',
    presetHeatwaveDesc: '+6°C तापमान विसंगती',
    presetCompoundDesc: 'पाऊस + उष्णता + पायाभूत सुविधा ताण',
    presetDrainageDesc: '40% निचरा सुधारणा',
    sliderDrought: 'दुष्काळ',
    sliderNormal: 'सामान्य',
    sliderExtreme: 'अत्यंत',
    sliderHeatwave: 'उष्णतेची लाट',
    sliderBlocked: 'अवरुद्ध',
    sliderImproved: 'सुधारित',
    sliderCurrent: 'सध्या',
    sliderGrowth: 'वाढ',
    sliderRapid: 'वेगवान',
    scenarioDescNeutral: 'सर्व पॅरामीटर आधाररेषेवर — परिस्थिती सिम्युलेट करण्यासाठी स्लायडर समायोजित करा किंवा प्रीसेट निवडा.',
    scenarioDescRainfall: 'पाऊस तीव्रता',
    scenarioDescReducedRain: 'कमी पाऊस',
    scenarioDescTempRise: 'तापमान वाढ',
    scenarioDescDegradedDrain: 'खराब निचरा',
    scenarioDescImprovedDrain: 'सुधारित निचरा',
    scenarioDescPopGrowth: 'लोकसंख्या वाढ',
    scenarioDescSimulating: 'सिम्युलेट होत आहे:',

    // ── New keys — Historical Validation ──────────────────────────────────
    histValidTitle: 'ऐतिहासिक घटना प्रमाणीकरण',
    histValidDesc: 'प्रत्यक्ष संग्रहित हवामान डेटा वापरून दस्तऐवजीकृत पुणे आपत्ती घटनांविरुद्ध आमच्या जोखीम मॉडेलचे प्रमाणीकरण करा',
    wardsAffected: 'वार्ड बाधित',
    rainfallMm: 'मिमी पाऊस',
    validationProgress: 'ओपन-मेटियो वरून संग्रहित हवामान आणले जात आहे → जोखीम मॉडेल चालवले जात आहे',
    modelPrediction: 'मॉडेल अंदाज',
    severityCatastrophic: 'आपत्तीजनक',
    severitySevere: 'गंभीर',
    severityModerate: 'मध्यम',

    // ── New keys — Decision Support ───────────────────────────────────────
    catDeploy: 'तैनात',
    catEvacuate: 'स्थलांतर',
    catAlert: 'सूचना',
    catMonitor: 'निरीक्षण',
    catPrepare: 'तयारी',
    assignedLabel: 'नियुक्त:',
    acknowledgeBtn: 'मान्य करा',
    acknowledgedLabel: 'मान्य केले',
    deployBtn: 'तैनात करा',

    // ── New keys — Misc ──────────────────────────────────────────────────
    clickCalculate: 'जोखीम गुण तयार करण्यासाठी "गणना करा" वर क्लिक करा',
    facilitiesLabel: 'सुविधा',
    capLabel: 'क्षमता',
    riskLabel: 'जोखीम',
    shelterLabel: 'निवारा',
    walkLabel: 'पायी',
    forWards: 'वार्ड',
  },
} as const;

export type TranslationKey = keyof typeof translations.en;

// Ward name helper — returns Marathi name when lang is hi/mr
export function wardName(
  obj: { ward_name: string; ward_name_marathi?: string },
  lang: Lang
): string {
  if (lang === 'en') return obj.ward_name;
  if (obj.ward_name_marathi) return obj.ward_name_marathi;
  // Fallback: lookup from static dictionary
  return WARD_NAME_DICT[obj.ward_name]?.[lang] ?? obj.ward_name;
}

// ── Ward name dictionary (for when backend doesn't send ward_name_marathi) ──
const WARD_NAME_DICT: Record<string, Record<string, string>> = {
  'Aundh':            { hi: 'औंध',           mr: 'औंध' },
  'Kothrud':          { hi: 'कोथरूड',        mr: 'कोथरूड' },
  'Shivajinagar':     { hi: 'शिवाजीनगर',     mr: 'शिवाजीनगर' },
  'Kasba Peth':       { hi: 'कसबा पेठ',      mr: 'कसबा पेठ' },
  'Hadapsar':         { hi: 'हडपसर',         mr: 'हडपसर' },
  'Kondhwa':          { hi: 'कोंढवा',        mr: 'कोंढवा' },
  'Bibwewadi':        { hi: 'बिबवेवाडी',     mr: 'बिबवेवाडी' },
  'Dhankawadi':       { hi: 'धनकवडी',        mr: 'धनकवडी' },
  'Warje':            { hi: 'वारजे',          mr: 'वारजे' },
  'Sinhagad Road':    { hi: 'सिंहगड रोड',    mr: 'सिंहगड रोड' },
  'Nagar Road':       { hi: 'नगर रोड',       mr: 'नगर रोड' },
  'Yerawada':         { hi: 'येरवडा',         mr: 'येरवडा' },
  'Dhole Patil Road': { hi: 'ढोले पाटील रोड', mr: 'ढोले पाटील रोड' },
  'Wanawadi':         { hi: 'वानवडी',         mr: 'वानवडी' },
  'Baner':            { hi: 'बाणेर',          mr: 'बाणेर' },
  'Balewadi':         { hi: 'बालेवाडी',       mr: 'बालेवाडी' },
  'Parvati':          { hi: 'पर्वती',          mr: 'पर्वती' },
  'Deccan Gymkhana':  { hi: 'डेक्कन जिमखाना', mr: 'डेक्कन जिमखाना' },
  'Kharadi':          { hi: 'खराडी',          mr: 'खराडी' },
  'Mundhwa':          { hi: 'मुंढवा',         mr: 'मुंढवा' },
  'Katraj':           { hi: 'कात्रज',         mr: 'कात्रज' },
  'Sahakarnagar':     { hi: 'सहकारनगर',      mr: 'सहकारनगर' },
};

// Hazard name helper
export function hazardKey(hazard: string): TranslationKey {
  switch (hazard) {
    case 'flood': return 'floodBtn';
    case 'heat': return 'heatBtn';
    default: return 'noneHazardLabel';
  }
}

// Severity key helper
export function severityKey(severity: string): TranslationKey {
  switch (severity) {
    case 'catastrophic': return 'severityCatastrophic';
    case 'severe': return 'severitySevere';
    case 'moderate': return 'severityModerate';
    default: return 'severityModerate';
  }
}

// Category key helper (decision support)
export function categoryKey(category: string): TranslationKey {
  switch (category) {
    case 'deploy': return 'catDeploy';
    case 'evacuate': return 'catEvacuate';
    case 'alert': return 'catAlert';
    case 'monitor': return 'catMonitor';
    case 'prepare': return 'catPrepare';
    default: return 'catMonitor';
  }
}

// Urgency label key helper (evacuation)
export function urgencyKey(urgency: string): TranslationKey {
  switch (urgency) {
    case 'immediate': return 'evacuateNow';
    case 'prepare': return 'prepare';
    case 'monitor': return 'monitor';
    case 'standby': return 'standby';
    default: return 'standby';
  }
}

// Route safety status helper
export function safetyStatusKey(status: string): TranslationKey {
  switch (status) {
    case 'safe': return 'safe';
    case 'moderate_risk': return 'moderateRiskStatus';
    default: return 'unsafeStatus';
  }
}

// Resource type name helper
export function resourceKey(type: string): TranslationKey {
  switch (type) {
    case 'pumps': return 'resPumps';
    case 'buses': return 'resBuses';
    case 'relief_camps': return 'resCamps';
    case 'cooling_centers': return 'resCooling';
    case 'medical_units': return 'resMedical';
    default: return 'resPumps';
  }
}

// Priority key helper (alerts)
export function priorityKey(priority: string): TranslationKey {
  switch (priority) {
    case 'emergency': return 'alertEmergency';
    case 'warning': return 'alertWarning';
    case 'watch': return 'alertWatch';
    case 'advisory': return 'alertAdvisory';
    default: return 'alertAdvisory';
  }
}

// Risk category key helper
export function riskCatKey(category: string): TranslationKey {
  switch(category) {
    case 'Low': return 'riskCatLow';
    case 'Moderate': return 'riskCatModerate';
    case 'High': return 'riskCatHigh';
    case 'Critical': return 'riskCatCritical';
    default: return 'riskCatLow';
  }
}

// Classification key helper
export function classKey(classification: string): TranslationKey {
  switch (classification) {
    case 'true_positive': return 'classTruePos';
    case 'false_positive': return 'classFalsePos';
    case 'true_negative': return 'classTrueNeg';
    case 'false_negative': return 'classFalseNeg';
    default: return 'classTrueNeg';
  }
}

// Trend key helper
export function trendKey(trend: string): TranslationKey {
  if (trend === 'rising') return 'trendRising';
  if (trend === 'falling') return 'trendFalling';
  return 'trendStable';
}

// ─────────────────────────────────────────────────────────────────────────────
// Context
// ─────────────────────────────────────────────────────────────────────────────
interface LangContextValue {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (key: TranslationKey) => string;
}

const LangContext = createContext<LangContextValue>({
  lang: 'en',
  setLang: () => {},
  t: (key) => translations.en[key],
});

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    return (localStorage.getItem('prakalp-lang') as Lang) || 'en';
  });

  const setLangPersist = (l: Lang) => {
    localStorage.setItem('prakalp-lang', l);
    setLang(l);
  };

  const t = (key: TranslationKey): string => translations[lang][key] as string;

  return (
    <LangContext.Provider value={{ lang, setLang: setLangPersist, t }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}

// ─────────────────────────────────────────────────────────────────────────────
// Language Toggle Component
// ─────────────────────────────────────────────────────────────────────────────
const LANGS: { code: Lang; label: string; native: string }[] = [
  { code: 'en', label: 'English', native: 'EN' },
  { code: 'hi', label: 'Hindi',   native: 'हि' },
  { code: 'mr', label: 'Marathi', native: 'म' },
];

export function LangToggle() {
  const { lang, setLang } = useLang();

  return (
    <div className="flex items-center gap-0 border-2 border-black overflow-hidden" title="Switch language">
      {LANGS.map((l) => (
        <button
          key={l.code}
          onClick={() => setLang(l.code)}
          title={l.label}
          className={`px-2.5 py-1 text-sm font-black transition-colors ${
            lang === l.code
              ? 'bg-black text-white'
              : 'bg-white text-black hover:bg-gray-100'
          }`}
        >
          {l.native}
        </button>
      ))}
    </div>
  );
}

// ═════════════════════════════════════════════════════════════════════════════
// Runtime translation helpers for backend-generated English text
// ═════════════════════════════════════════════════════════════════════════════

// ── Risk Factor Names ──────────────────────────────────────────────────────
const FACTOR_NAMES: Record<string, Record<Lang, string>> = {
  rainfall_intensity:      { en: 'Rainfall Intensity',        hi: 'वर्षा तीव्रता',               mr: 'पावसाची तीव्रता' },
  cumulative_rainfall_48h: { en: '48h Cumulative Rainfall',   hi: '48 घंटे संचयी वर्षा',         mr: '48 तास एकूण पाऊस' },
  elevation_m:             { en: 'Elevation',                 hi: 'ऊंचाई',                       mr: 'उंची' },
  mean_slope:              { en: 'Terrain Slope',             hi: 'भूमि ढलान',                   mr: 'भूप्रदेश उतार' },
  drainage_index:          { en: 'Drainage Index',            hi: 'जल निकासी सूचकांक',           mr: 'निचरा निर्देशांक' },
  impervious_surface_pct:  { en: 'Impervious Surface %',     hi: 'अभेद्य सतह %',               mr: 'अभेद्य पृष्ठभाग %' },
  low_lying_index:         { en: 'Low-lying Index',           hi: 'निचला क्षेत्र सूचकांक',       mr: 'सखल प्रदेश निर्देशांक' },
  historical_frequency:    { en: 'Historical Frequency',     hi: 'ऐतिहासिक आवृत्ति',             mr: 'ऐतिहासिक वारंवारता' },
  population_density:      { en: 'Population Density',       hi: 'जनसंख्या घनत्व',              mr: 'लोकसंख्या घनता' },
  elderly_ratio:           { en: 'Elderly Population Ratio', hi: 'वृद्ध जनसंख्या अनुपात',       mr: 'वृद्ध लोकसंख्या प्रमाण' },
  infrastructure_density:  { en: 'Infrastructure Density',   hi: 'बुनियादी ढांचा घनत्व',        mr: 'पायाभूत सुविधा घनता' },
  // human-readable names from old engine
  'Forecast Rainfall Intensity':  { en: 'Forecast Rainfall Intensity',  hi: 'पूर्वानुमानित वर्षा तीव्रता',        mr: 'अंदाजित पाऊस तीव्रता' },
  '48-Hour Cumulative Rainfall':  { en: '48-Hour Cumulative Rainfall',  hi: '48 घंटे संचयी वर्षा',                mr: '48 तास एकूण पाऊस' },
  'Baseline Vulnerability':       { en: 'Baseline Vulnerability',       hi: 'आधारभूत संवेदनशीलता',                  mr: 'आधारभूत असुरक्षितता' },
  'Historical Flood Frequency':   { en: 'Historical Flood Frequency',   hi: 'ऐतिहासिक बाढ़ आवृत्ति',               mr: 'ऐतिहासिक पूर वारंवारता' },
  'Elevation Vulnerability':      { en: 'Elevation Vulnerability',      hi: 'ऊंचाई संवेदनशीलता',                   mr: 'उंची असुरक्षितता' },
  'Drainage Weakness':            { en: 'Drainage Weakness',            hi: 'जल निकासी कमजोरी',                   mr: 'निचरा कमकुवतपणा' },
  'Temperature Anomaly':          { en: 'Temperature Anomaly',          hi: 'तापमान विसंगति',                       mr: 'तापमान विसंगती' },
  'Historical Heatwave Frequency':{ en: 'Historical Heatwave Frequency',hi: 'ऐतिहासिक लू आवृत्ति',                 mr: 'ऐतिहासिक उष्णतेची लाट वारंवारता' },
  'Elderly Population Ratio':     { en: 'Elderly Population Ratio',     hi: 'वृद्ध जनसंख्या अनुपात',               mr: 'वृद्ध लोकसंख्या प्रमाण' },
  'Population Density':           { en: 'Population Density',           hi: 'जनसंख्या घनत्व',                      mr: 'लोकसंख्या घनता' },
  'Rainfall intensity':           { en: 'Rainfall intensity',           hi: 'वर्षा तीव्रता',                       mr: 'पावसाची तीव्रता' },
  '48h cumulative rainfall':      { en: '48h cumulative rainfall',      hi: '48 घंटे संचयी वर्षा',                 mr: '48 तास एकूण पाऊस' },
  'Historical vulnerability':     { en: 'Historical vulnerability',     hi: 'ऐतिहासिक संवेदनशीलता',                 mr: 'ऐतिहासिक असुरक्षितता' },
};

/** Translate a risk factor name */
export function translateFactor(factor: string, lang: Lang): string {
  if (lang === 'en') return FACTOR_NAMES[factor]?.en ?? factor.replace(/_/g, ' ');
  return FACTOR_NAMES[factor]?.[lang] ?? factor.replace(/_/g, ' ');
}

// ── Recommendation translations ────────────────────────────────────────────
const RECOMMENDATIONS: Record<string, Record<Lang, string>> = {
  'Activate emergency response protocols immediately':                { en: 'Activate emergency response protocols immediately',                hi: 'तत्काल आपातकालीन प्रतिक्रिया प्रोटोकॉल सक्रिय करें',           mr: 'तात्काळ आपत्कालीन प्रतिसाद प्रोटोकॉल सक्रिय करा' },
  'Issue public warning for all residents':                           { en: 'Issue public warning for all residents',                           hi: 'सभी निवासियों के लिए सार्वजनिक चेतावनी जारी करें',           mr: 'सर्व रहिवाशांसाठी सार्वजनिक इशारा जारी करा' },
  'Deploy water pumps to low-lying areas':                            { en: 'Deploy water pumps to low-lying areas',                            hi: 'निचले क्षेत्रों में पानी के पंप तैनात करें',                    mr: 'सखल भागात पाण्याचे पंप तैनात करा' },
  'Clear blocked drainage channels immediately':                      { en: 'Clear blocked drainage channels immediately',                      hi: 'तत्काल अवरुद्ध जल निकासी चैनल साफ करें',                      mr: 'अवरोधित निचरा वाहिन्या तात्काळ साफ करा' },
  'Prepare evacuation buses for flood-prone zones':                   { en: 'Prepare evacuation buses for flood-prone zones',                   hi: 'बाढ़-प्रवण क्षेत्रों के लिए निकासी बसें तैयार करें',           mr: 'पूर-प्रवण भागांसाठी स्थलांतर बस तयार करा' },
  'Activate cooling centers in the ward':                             { en: 'Activate cooling centers in the ward',                             hi: 'वार्ड में कूलिंग सेंटर सक्रिय करें',                            mr: 'वार्डात शीतकेंद्रे सक्रिय करा' },
  'Deploy health workers for elderly welfare checks':                 { en: 'Deploy health workers for elderly welfare checks',                 hi: 'वृद्धों की कल्याण जांच के लिए स्वास्थ्य कर्मी तैनात करें',     mr: 'वृद्धांच्या कल्याण तपासणीसाठी आरोग्य कर्मचारी तैनात करा' },
  'Ensure water distribution points are operational':                 { en: 'Ensure water distribution points are operational',                 hi: 'सुनिश्चित करें कि जल वितरण बिंदु चालू हैं',                     mr: 'पाणी वितरण केंद्रे कार्यरत आहेत याची खात्री करा' },
  'Alert hospitals for potential casualty surge':                     { en: 'Alert hospitals for potential casualty surge',                     hi: 'संभावित हताहत वृद्धि के लिए अस्पतालों को सतर्क करें',           mr: 'संभाव्य जखमी वाढीसाठी रुग्णालयांना सतर्क करा' },
  'Increase monitoring frequency to every 10 minutes':               { en: 'Increase monitoring frequency to every 10 minutes',               hi: 'निगरानी आवृत्ति हर 10 मिनट तक बढ़ाएं',                           mr: 'निरीक्षण वारंवारता दर 10 मिनिटांपर्यंत वाढवा' },
  'Continue monitoring, assess again in 30 minutes':                  { en: 'Continue monitoring, assess again in 30 minutes',                  hi: 'निगरानी जारी रखें, 30 मिनट में पुनः मूल्यांकन करें',            mr: 'निरीक्षण सुरू ठेवा, 30 मिनिटांत पुन्हा मूल्यांकन करा' },
  'Risk levels within normal range. Maintain standard monitoring.':   { en: 'Risk levels within normal range. Maintain standard monitoring.',   hi: 'जोखिम स्तर सामान्य सीमा में। मानक निगरानी बनाए रखें।',         mr: 'जोखीम पातळी सामान्य मर्यादेत. मानक निरीक्षण सुरू ठेवा.' },
  // Old engine recs - flood
  'Immediate evacuation of low-lying areas':                          { en: 'Immediate evacuation of low-lying areas',                          hi: 'निचले क्षेत्रों से तत्काल निकासी',                               mr: 'सखल भागांतून तात्काळ स्थलांतर' },
  'Deploy all available pumps to critical locations':                 { en: 'Deploy all available pumps to critical locations',                 hi: 'सभी उपलब्ध पंप महत्वपूर्ण स्थानों पर तैनात करें',              mr: 'सर्व उपलब्ध पंप गंभीर ठिकाणी तैनात करा' },
  'Open relief camps and mobilize buses':                             { en: 'Open relief camps and mobilize buses',                             hi: 'राहत शिविर खोलें और बसें तैयार करें',                            mr: 'मदत शिबिरे उघडा आणि बस तयार करा' },
  'Alert medical teams for emergency response':                      { en: 'Alert medical teams for emergency response',                      hi: 'आपातकालीन प्रतिक्रिया के लिए चिकित्सा दलों को सतर्क करें',     mr: 'आपत्कालीन प्रतिसादासाठी वैद्यकीय पथकांना सतर्क करा' },
  'Pre-position pumps and sandbags':                                  { en: 'Pre-position pumps and sandbags',                                  hi: 'पंप और बालू के थैले पहले से तैनात करें',                         mr: 'पंप आणि वाळूच्या पिशव्या आधीपासून तैनात करा' },
  'Alert relief camp managers':                                      { en: 'Alert relief camp managers',                                      hi: 'राहत शिविर प्रबंधकों को सतर्क करें',                             mr: 'मदत शिबिर व्यवस्थापकांना सतर्क करा' },
  'Monitor water levels hourly':                                     { en: 'Monitor water levels hourly',                                     hi: 'हर घंटे जल स्तर की निगरानी करें',                                 mr: 'दर तासाला पाण्याच्या पातळीचे निरीक्षण करा' },
  'Prepare vulnerable population for possible evacuation':           { en: 'Prepare vulnerable population for possible evacuation',           hi: 'कमजोर आबादी को संभावित निकासी के लिए तैयार करें',               mr: 'असुरक्षित लोकसंख्येला संभाव्य स्थलांतरासाठी तयार करा' },
  'Increase monitoring frequency':                                   { en: 'Increase monitoring frequency',                                   hi: 'निगरानी आवृत्ति बढ़ाएं',                                         mr: 'निरीक्षण वारंवारता वाढवा' },
  'Verify drainage clearance':                                       { en: 'Verify drainage clearance',                                       hi: 'जल निकासी मंजूरी सत्यापित करें',                                 mr: 'निचरा मार्ग मोकळा आहे ते तपासा' },
  'Brief response teams':                                            { en: 'Brief response teams',                                            hi: 'प्रतिक्रिया दलों को जानकारी दें',                                 mr: 'प्रतिसाद पथकांना माहिती द्या' },
  'Maintain normal monitoring':                                      { en: 'Maintain normal monitoring',                                      hi: 'सामान्य निगरानी बनाए रखें',                                       mr: 'सामान्य निरीक्षण सुरू ठेवा' },
  // Old engine recs - heat
  'Activate all cooling centers immediately':                        { en: 'Activate all cooling centers immediately',                        hi: 'तत्काल सभी कूलिंग सेंटर सक्रिय करें',                           mr: 'सर्व शीतकेंद्रे तात्काळ सक्रिय करा' },
  'Issue public heat alert':                                         { en: 'Issue public heat alert',                                         hi: 'सार्वजनिक गर्मी चेतावनी जारी करें',                               mr: 'सार्वजनिक उष्णता इशारा जारी करा' },
  'Deploy mobile medical units':                                     { en: 'Deploy mobile medical units',                                     hi: 'मोबाइल चिकित्सा इकाइयां तैनात करें',                             mr: 'फिरते वैद्यकीय पथक तैनात करा' },
  'Conduct vulnerable population check-ins':                         { en: 'Conduct vulnerable population check-ins',                         hi: 'कमजोर आबादी की जांच करें',                                       mr: 'असुरक्षित लोकसंख्येची तपासणी करा' },
  'Open designated cooling centers':                                 { en: 'Open designated cooling centers',                                 hi: 'नामित कूलिंग सेंटर खोलें',                                       mr: 'नियुक्त शीतकेंद्रे उघडा' },
  'Distribute water at public locations':                            { en: 'Distribute water at public locations',                            hi: 'सार्वजनिक स्थानों पर पानी वितरित करें',                           mr: 'सार्वजनिक ठिकाणी पाणी वाटप करा' },
  'Alert healthcare facilities':                                     { en: 'Alert healthcare facilities',                                     hi: 'स्वास्थ्य सुविधाओं को सतर्क करें',                                 mr: 'आरोग्य सुविधांना सतर्क करा' },
  'Priority outreach to elderly population':                         { en: 'Priority outreach to elderly population',                         hi: 'वृद्ध आबादी तक प्राथमिकता से पहुंच',                             mr: 'वृद्ध लोकसंख्येपर्यंत प्राधान्य पोहोच' },
};

/** Translate a recommendation string */
export function translateRecommendation(rec: string, lang: Lang): string {
  if (lang === 'en') return rec;
  return RECOMMENDATIONS[rec]?.[lang] ?? rec;
}

// ── Surge description translations ─────────────────────────────────────────
/** Translate surge_description from the backend */
export function translateSurge(desc: string, lang: Lang): string {
  if (lang === 'en' || !desc) return desc;
  // Pattern matching for template-based surge descriptions
  if (desc.startsWith('CRITICAL SURGE:')) {
    const pct = desc.match(/(\d+)%/)?.[1] ?? '';
    return lang === 'hi'
      ? `गंभीर उछाल: आधारभूत से ${pct}% ऊपर जोखिम बढ़ गया`
      : `गंभीर उसळी: जोखीम आधारभूतपेक्षा ${pct}% वाढली`;
  }
  if (desc.startsWith('RISK SURGE:')) {
    const pct = desc.match(/(\d+)%/)?.[1] ?? '';
    return lang === 'hi'
      ? `जोखिम उछाल: आधारभूत से ${pct}% ऊपर जोखिम बढ़ गया`
      : `जोखीम उसळी: आधारभूतपेक्षा ${pct}% वाढ`;
  }
  if (desc.startsWith('Elevated:')) {
    const pct = desc.match(/(\d+)%/)?.[1] ?? '';
    return lang === 'hi'
      ? `बढ़ा हुआ: आधारभूत से ${pct}% ऊपर`
      : `वाढीव: आधारभूतपेक्षा ${pct}% वर`;
  }
  if (desc.includes('within normal range')) {
    return lang === 'hi' ? 'जोखिम सामान्य सीमा में' : 'जोखीम सामान्य मर्यादेत';
  }
  if (desc.includes('CRITICAL SURGE: Immediate action')) {
    return lang === 'hi' ? 'गंभीर उछाल: तत्काल कार्रवाई आवश्यक' : 'गंभीर उसळी: तात्काळ कारवाई आवश्यक';
  }
  if (desc.includes('ESCALATION ALERT')) {
    return lang === 'hi' ? 'वृद्धि चेतावनी: जोखिम आधारभूत से काफी ऊपर' : 'वाढीची सूचना: जोखीम आधारभूतपेक्षा लक्षणीय वर';
  }
  if (desc.includes('CRITICAL HEAT SURGE')) {
    return lang === 'hi' ? 'गंभीर गर्मी उछाल: तत्काल कूलिंग उपाय आवश्यक' : 'गंभीर उष्णता उसळी: तात्काळ थंडावा उपाय आवश्यक';
  }
  if (desc.includes('HEAT ESCALATION')) {
    return lang === 'hi' ? 'गर्मी वृद्धि: बढ़ी निगरानी आवश्यक' : 'उष्णता वाढ: वाढीव निरीक्षण आवश्यक';
  }
  return desc;
}

// ── Narrative text translation ─────────────────────────────────────────────
/** Translate the explanation narrative from the backend */
export function translateNarrative(narrative: string, lang: Lang): string {
  if (lang === 'en' || !narrative) return narrative;

  let translated = narrative;

  // Replace ward names
  for (const [en, translations] of Object.entries(WARD_NAME_DICT)) {
    if (translated.includes(en)) {
      translated = translated.replace(new RegExp(en, 'g'), translations[lang] ?? en);
    }
  }

  // Replace common narrative phrases
  const PHRASES: [RegExp, Record<string, string>][] = [
    [/is currently at (\d+(?:\.\d+)?)% flood risk/g, {
      hi: '$1% बाढ़ जोखिम पर है',
      mr: '$1% पूर जोखीम आहे',
    }],
    [/is currently at (\d+(?:\.\d+)?)% heat risk/g, {
      hi: '$1% गर्मी जोखिम पर है',
      mr: '$1% उष्णता जोखीम आहे',
    }],
    [/\(baseline: (\d+(?:\.\d+)?)%\)/g, {
      hi: '(आधारभूत: $1%)',
      mr: '(आधारभूत: $1%)',
    }],
    [/Risk has increased by (\d+(?:\.\d+)?)% due to current weather conditions/g, {
      hi: 'वर्तमान मौसम स्थितियों के कारण जोखिम $1% बढ़ गया है',
      mr: 'सध्याच्या हवामान परिस्थितीमुळे जोखीम $1% वाढली आहे',
    }],
    [/Risk is (\d+(?:\.\d+)?)% below baseline due to favorable conditions/g, {
      hi: 'अनुकूल परिस्थितियों के कारण जोखिम आधारभूत से $1% नीचे है',
      mr: 'अनुकूल परिस्थितीमुळे जोखीम आधारभूतपेक्षा $1% कमी आहे',
    }],
    [/Risk is at baseline levels/g, {
      hi: 'जोखिम आधारभूत स्तर पर है',
      mr: 'जोखीम आधारभूत पातळीवर आहे',
    }],
    [/The primary risk driver is (.+)\./g, {
      hi: 'प्राथमिक जोखिम कारक $1 है।',
      mr: 'प्राथमिक जोखीम कारक $1 आहे.',
    }],
    // Old engine narratives
    [/is experiencing a CRITICAL flood risk surge/g, {
      hi: 'गंभीर बाढ़ जोखिम उछाल अनुभव कर रहा है',
      mr: 'गंभीर पूर जोखीम उसळीचा अनुभव घेत आहे',
    }],
    [/shows elevated flood risk/g, {
      hi: 'बढ़ा हुआ बाढ़ जोखिम दर्शाता है',
      mr: 'वाढीव पूर जोखीम दर्शवते',
    }],
    [/flood risk is near baseline levels/g, {
      hi: 'बाढ़ जोखिम आधारभूत स्तर के करीब है',
      mr: 'पूर जोखीम आधारभूत पातळीजवळ आहे',
    }],
    [/is under CRITICAL heat stress/g, {
      hi: 'गंभीर गर्मी तनाव में है',
      mr: 'गंभीर उष्णता ताणाखाली आहे',
    }],
    [/experiencing elevated heat risk/g, {
      hi: 'बढ़ा हुआ गर्मी जोखिम अनुभव कर रहा है',
      mr: 'वाढीव उष्णता जोखीम अनुभवत आहे',
    }],
    [/heat risk at normal levels/g, {
      hi: 'गर्मी जोखिम सामान्य स्तर पर',
      mr: 'उष्णता जोखीम सामान्य पातळीवर',
    }],
    [/Current risk[:\s]+(\d+(?:\.\d+)?)%/g, {
      hi: 'वर्तमान जोखिम: $1%',
      mr: 'सध्याची जोखीम: $1%',
    }],
    [/Baseline[:\s]+(\d+(?:\.\d+)?)%/g, {
      hi: 'आधारभूत: $1%',
      mr: 'आधारभूत: $1%',
    }],
    [/Primary driver: (.+?)\./g, {
      hi: 'प्राथमिक कारक: $1।',
      mr: 'प्राथमिक कारक: $1.',
    }],
    [/Immediate evacuation and resource deployment recommended/g, {
      hi: 'तत्काल निकासी और संसाधन तैनाती अनुशंसित',
      mr: 'तात्काळ स्थलांतर आणि संसाधन तैनाती शिफारस',
    }],
    [/Pre-position resources and alert response teams/g, {
      hi: 'संसाधन पूर्व-तैनात करें और प्रतिक्रिया दलों को सतर्क करें',
      mr: 'संसाधने आधीपासून तैनात करा आणि प्रतिसाद पथकांना सतर्क करा',
    }],
    [/Maintain normal monitoring procedures/g, {
      hi: 'सामान्य निगरानी प्रक्रिया बनाए रखें',
      mr: 'सामान्य निरीक्षण प्रक्रिया सुरू ठेवा',
    }],
    [/Activate cooling centers and issue heat alerts immediately/g, {
      hi: 'तत्काल कूलिंग सेंटर सक्रिय करें और गर्मी चेतावनी जारी करें',
      mr: 'तात्काळ शीतकेंद्रे सक्रिय करा आणि उष्णता इशारा जारी करा',
    }],
    [/Prepare cooling infrastructure and vulnerable population outreach/g, {
      hi: 'कूलिंग बुनियादी ढांचा और कमजोर आबादी तक पहुंच तैयार करें',
      mr: 'शीतकरण पायाभूत सुविधा आणि असुरक्षित लोकसंख्येपर्यंत पोहोच तयार करा',
    }],
    [/percentage points above baseline/g, {
      hi: 'प्रतिशत अंक आधारभूत से ऊपर',
      mr: 'टक्के गुण आधारभूतपेक्षा वर',
    }],
    [/Key factor: /g, {
      hi: 'मुख्य कारक: ',
      mr: 'मुख्य कारक: ',
    }],
  ];

  for (const [pattern, replacement] of PHRASES) {
    const rep = replacement[lang];
    if (rep) {
      translated = translated.replace(pattern, rep);
    }
  }

  // Also translate factor names that appear inside narratives
  for (const [factorEn, translations] of Object.entries(FACTOR_NAMES)) {
    if (translated.includes(factorEn)) {
      translated = translated.replace(new RegExp(factorEn.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), translations[lang] ?? factorEn);
    }
  }

  return translated;
}

// ── Historical event translations ──────────────────────────────────────────
const HISTORICAL_EVENTS: Record<string, Record<Lang, { name: string; description: string }>> = {
  'Pune September 2019 Floods': {
    en: { name: 'Pune September 2019 Floods', description: 'Extreme rainfall caused Ambil Odha nallah overflow. Katraj, Bibwewadi, Sahakarnagar submerged. 21 deaths, 12,000+ rescued. 200mm+ rainfall in 24h.' },
    hi: { name: 'पुणे सितम्बर 2019 बाढ़', description: 'अत्यधिक वर्षा से आम्बिल ओढा नाला उफान पर आया। कात्रज, बिबवेवाडी, सहकारनगर जलमग्न। 21 मृत्यु, 12,000+ बचाए गए। 24 घंटे में 200mm+ वर्षा।' },
    mr: { name: 'पुणे सप्टेंबर 2019 पूर', description: 'अत्यंत पावसामुळे आंबिल ओढा नाला ओसंडून वाहिला. कात्रज, बिबवेवाडी, सहकारनगर जलमय. 21 मृत्यू, 12,000+ बचावले. 24 तासांत 200mm+ पाऊस.' },
  },
  'Pune October 2020 Heavy Rains': {
    en: { name: 'Pune October 2020 Heavy Rains', description: 'Incessant rainfall causing waterlogging in low-lying areas. Bibwewadi, Sahakarnagar, Hadapsar, Kondhwa heavily affected. Water entered ground floors.' },
    hi: { name: 'पुणे अक्टूबर 2020 भारी बारिश', description: 'लगातार बारिश से निचले इलाकों में जलभराव। बिबवेवाडी, सहकारनगर, हडपसर, कोंढवा बुरी तरह प्रभावित। भूतल में पानी भर गया।' },
    mr: { name: 'पुणे ऑक्टोबर 2020 मुसळधार पाऊस', description: 'सतत पावसामुळे सखल भागात पाणी साचले. बिबवेवाडी, सहकारनगर, हडपसर, कोंढवा गंभीर रूपे प्रभावित. तळमजल्यात पाणी शिरले.' },
  },
  'Pune July 2023 Flash Floods': {
    en: { name: 'Pune July 2023 Flash Floods', description: 'Sudden heavy downpour flooded Hadapsar, Kondhwa, Bibwewadi, Katraj areas. Mula-Mutha rivers rose sharply. Vehicles swept in low-lying zones.' },
    hi: { name: 'पुणे जुलाई 2023 अचानक बाढ़', description: 'अचानक भारी बारिश से हडपसर, कोंढवा, बिबवेवाडी, कात्रज में बाढ़। मुला-मुठा नदियां तेजी से बढ़ीं। निचले इलाकों में वाहन बह गए।' },
    mr: { name: 'पुणे जुलै 2023 अचानक पूर', description: 'अचानक मुसळधार पावसाने हडपसर, कोंढवा, बिबवेवाडी, कात्रज परिसर पाण्याखाली. मुळा-मुठा नद्या झपाट्याने वाढल्या. सखल भागात वाहने वाहून गेली.' },
  },
  'Pune April 2024 Heatwave': {
    en: { name: 'Pune April 2024 Heatwave', description: '7-day heatwave with temperatures exceeding 42°C. Multiple heat-stroke cases. Water supply disrupted in eastern wards.' },
    hi: { name: 'पुणे अप्रैल 2024 लू', description: '42°C से अधिक तापमान वाली 7 दिन की लू। कई लू से बीमारी के मामले। पूर्वी वार्डों में पानी आपूर्ति बाधित।' },
    mr: { name: 'पुणे एप्रिल 2024 उष्णतेची लाट', description: '42°C पेक्षा जास्त तापमानासह 7 दिवसांची उष्णतेची लाट. अनेक उष्माघात प्रकरणे. पूर्व वार्डांमध्ये पाणीपुरवठा विस्कळीत.' },
  },
  'Pune September 2024 Waterlogging': {
    en: { name: 'Pune September 2024 Waterlogging', description: 'Heavy pre-monsoon rains caused widespread waterlogging in low-lying wards. Khadakwasla dam release added to flood risk in downstream low-elevation wards.' },
    hi: { name: 'पुणे सितम्बर 2024 जलभराव', description: 'भारी प्री-मानसून बारिश से निचले वार्डों में व्यापक जलभराव। खडकवासला बांध से पानी छोड़ने से निचले ऊंचाई वाले वार्डों में बाढ़ का खतरा बढ़ा।' },
    mr: { name: 'पुणे सप्टेंबर 2024 पाणी साचणे', description: 'मुसळधार पूर्व-मान्सून पावसामुळे सखल वार्डांमध्ये मोठ्या प्रमाणावर पाणी साचले. खडकवासला धरणातून पाणी सोडल्याने खालच्या भागातील वार्डांमध्ये पूर जोखीम वाढली.' },
  },
};

/** Translate a historical event name */
export function translateEventName(name: string, lang: Lang): string {
  if (lang === 'en') return name;
  return HISTORICAL_EVENTS[name]?.[lang]?.name ?? name;
}

/** Translate a historical event description */
export function translateEventDesc(name: string, description: string, lang: Lang): string {
  if (lang === 'en') return description;
  return HISTORICAL_EVENTS[name]?.[lang]?.description ?? description;
}
