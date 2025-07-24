**************************************************************************;
* Program name      : qs.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.qs and sdtm.suppqs
*
* Author            : Zifan Guo (knfg575)
*
* Date created      : 2024-06-04
*
* Input datasets    : RAW.OCULQ, RAW.REVPRDI, RAW.KPSS, RAW.KCCQ, RAW.COMPASS,
                      RAW.EQ_5D_5L, RAW.NFQOLDN

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : qs.sas7bdat, suppqs.sas7bdat
*
* Usage notes       :  
**************************************************************************;

%setup(version=260,
       localsetup=root/cdar/%scan(&_exec_programpath.,3,/)/%scan(&_exec_programpath.,4,/)/ar/%scan(&_exec_programpath.,6,/)/common/dev/macro/localsetup.sas);

%localsetup;

proc datasets lib=work kill nowarn nodetails nolist mt=data;
quit;

%let PGMNAME=%scan(&_EXEC_PROGRAMNAME,1, ".");
%let domain = %upcase(&pgmname.);

%procprint_indi;

/* proc transpose data=raw.eq_5d_5l_tmp out=raw_qs10n(rename=(col1=resn) drop=_name_); */
/* by study subject visit vis_dat qscat qscevint qsmethod qsdat qstim; */
/* var eq5d0201; */
/* format visit; */
/* run; */

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
options symbolgen;
%sdtm_initfmt(rawdata=eq_5d_5l compass kccq nfqoldn kpss oculq);

/*Step 2: Shell for SDTM derivation*/
/* data &pgmname._raw; */
/*  set raw.oculq raw.revprdi raw.kpss; */
/*  */
/* run; */
data eq_5d_5l;
    set eq_5d_5l;
    length eq5d206c $200.;
    label eq5d206c="EQ5D02-EQ VAS Score";
    format visit;
    eq5d206c = strip(put(eq5d0206,best.));
    proc sort; by study subject visit vis_dat qscat qscevint qsmethod qsdat qstim;
run;
proc transpose data=eq_5d_5l out=raw_qs10(rename=(_name_=qstestcd _label_=qstest col1=res));
by study subject visit vis_dat qscat qscevint qsmethod qsdat qstim;
var eq5d0201-eq5d0205 eq5d206c;
run;

proc sort data=raw.eq_5d_5l out=raw_eq_5d_5l; 
by study subject visit vis_dat qscat qscevint qsmethod qsdat qstim;
run;

proc transpose data=raw_eq_5d_5l out=raw_qs10n(rename=(col1=resn) drop=_name_ _label_);
format visit;
by study subject visit vis_dat qscat qscevint qsmethod qsdat qstim;
var eq5d0201-eq5d0206;
run;

data __raw_qs1 (drop=resn);
    merge raw_qs10 raw_qs10n;
    length qsorres qsstresc $200.;
    qsorres = strip(res);
    qsstresc = strip(put(resn,best.));
    qsstresn = resn;
run;

proc sort data=compass; by study subject visit vis_dat qscat qsdat qstim;
proc transpose data=compass (drop=com0117B com0121B com0124B com0125B com0126B) out=raw_qs20(rename=(_name_=qstestcd _label_=qstest col1=res));
format visit;
by study subject visit vis_dat qscat qsdat qstim;
var com:;
run;

data __raw_qs2;
    set raw_qs20;
    length qsorres qsstresc $200.;
    qsorres = strip(res);
    if qsorres = "." then qsorres = "";
    qsstresc = qsorres;
    if qstestcd = "COM0106A" then qstest = "Body Affected by Color Changes (Hands)";
    else if qstestcd = "COM0106B" then qstest = "Body Affected by Color Changes (Feet)";
run;

data raw_qs2_supp;
set raw.compass (keep=study subject visit vis_dat qscat qsdat qstim com0117B com0121B com0124B com0125B com0126B);
format visit;
run;

proc sort data=kccq; by study subject visit vis_dat qscat qsdat qstim;
proc transpose data=kccq out=raw_qs30(rename=(_name_=qstestcd _label_=qstest col1=res));
format visit;
by study subject visit vis_dat qscat qsdat qstim;
var kccq:;
run;

proc sort data=raw.kccq out=raw_kccq; by study subject visit vis_dat qscat qsdat qstim;
proc transpose data=raw_kccq out=raw_qs30n(rename=(col1=resn) drop=_name_ _label_);
format visit;
by study subject visit vis_dat qscat qsdat qstim;
var kccq:;
run;

data __raw_qs3 (drop=resn);
    merge raw_qs30 raw_qs30n;
    length qsorres qsstresc $200.;
    qsorres = strip(res);
    qsstresc = qsorres;
    qsstresn = /*resn*/ .;
run;

proc sort data=nfqoldn; by study subject visit vis_dat qscat qsdat qstim;
proc transpose data=nfqoldn out=raw_qs40(rename=(_name_=qstestcd _label_=qstest col1=qsorres));
format visit;
by study subject visit vis_dat qscat qsdat qstim;
var nfq:;
run;

proc sort data=raw.nfqoldn out=raw_nfqoldn; by study subject visit vis_dat qscat qsdat qstim;
proc transpose data=raw_nfqoldn out=raw_qs40n(rename=(col1=resn) drop=_name_ _label_);
format visit;
by study subject visit vis_dat qscat qsdat qstim;
var nfq:;
run;

data __raw_qs4;
    merge raw_qs40 raw_qs40n;
    length qsorres qsstresc $200.;
    qsstresc = qsorres;
    qsstresn = /*input(resn,??best.)*/ .;
    if qstestcd = "NFQ0117" then qstest = "Unable to Tell Hot From Cold Water_hand";
    else if qstestcd = "NFQ0118" then qstest = "Unable to Tell Hot From Cold Water_feet";
run;

proc transpose data=kpss out=raw_qs50(rename=(_name_=qstestcd _label_=qstest col1=qsorres));
format visit;
by study subject module module_o visit vis_dat qscat qseval qsdat qsmoth qsmreas;
var kpss:;
run;

proc transpose data=raw.kpss out=raw_qs50n(rename=(_name_=qstestcd _label_=qstest col1=resn));
format visit;
by study subject module module_o visit vis_dat qscat qseval qsdat qsmoth qsmreas;
var kpss:;
run;

data __raw_qs5 (drop=resn);
    merge raw_qs50 raw_qs50n;
    length qsstresc $200.;
    qsstresc = strip(resn);
    qsstresn = input(resn,??best.);
run;

proc transpose data=oculq out=raw_qs60(rename=(_name_=qstestcd _label_=qstest col1=qsorres oculqcat=qscat oculqdat=qsdat));
format visit;
by study subject module module_o visit vis_dat oculqcat oculqyn oculqdat;
var oculq0:;
run;

data __raw_qs6;
    set raw_qs60;
    length qsstresc $200.;
    qsstresc = qsorres;
run;

data qs0 (drop=res);
    length qstim $8. qstest $200.;
    set __raw_qs: raw.revprdi (where=(qscstat="0"));
run;

proc sort data=qs0; by study subject visit vis_dat qscat qsdat qstim; run;
proc sort data=raw_qs2_supp; by study subject visit vis_dat qscat qsdat qstim; run;

data qs1;
    merge qs0 raw_qs2_supp;
    by study subject visit vis_dat qscat qsdat qstim;
run;
%sdtm_init(domain=qs, rawdata=qs1, outdata=qs2);

proc format;
    value $qsscat
    'KCCQ101A'='PHYSICAL LIMITATION'
'KCCQ101B'='PHYSICAL LIMITATION'
'KCCQ101C'='PHYSICAL LIMITATION'
'KCCQ101D'='PHYSICAL LIMITATION'
'KCCQ101E'='PHYSICAL LIMITATION'
'KCCQ101F'='PHYSICAL LIMITATION'
'KCCQ102'='SYMPTOM STABILITY'
'KCCQ103'='SYMPTOM FREQUENCY'
'KCCQ104'='SYMPTOM BURDEN'
'KCCQ105'='SYMPTOM FREQUENCY'
'KCCQ106'='SYMPTOM BURDEN'
'KCCQ107'='SYMPTOM FREQUENCY'
'KCCQ108'='SYMPTOM BURDEN'
'KCCQ109'='SYMPTOM FREQUENCY'
'KCCQ110'='SELF-EFFICACY'
'KCCQ111'='SELF-EFFICACY'
'KCCQ112'='QUALITY OF LIFE'
'KCCQ113'='QUALITY OF LIFE'
'KCCQ114'='QUALITY OF LIFE'
'KCCQ115A'='SOCIAL LIMITATION'
'KCCQ115B'='SOCIAL LIMITATION'
'KCCQ115C'='SOCIAL LIMITATION'
'KCCQ115D'='SOCIAL LIMITATION'
'NFQ0101A'='SYMPTOMS'
'NFQ0101B'='SYMPTOMS'
'NFQ0101C'='SYMPTOMS'
'NFQ0101D'='SYMPTOMS'
'NFQ0101E'='SYMPTOMS'
'NFQ0102A'='SYMPTOMS'
'NFQ0102B'='SYMPTOMS'
'NFQ0102C'='SYMPTOMS'
'NFQ0102D'='SYMPTOMS'
'NFQ0102E'='SYMPTOMS'
'NFQ0103A'='SYMPTOMS'
'NFQ0103B'='SYMPTOMS'
'NFQ0103C'='SYMPTOMS'
'NFQ0103D'='SYMPTOMS'
'NFQ0103E'='SYMPTOMS'
'NFQ0104A'='SYMPTOMS'
'NFQ0104B'='SYMPTOMS'
'NFQ0104C'='SYMPTOMS'
'NFQ0104D'='SYMPTOMS'
'NFQ0104E'='SYMPTOMS'
'NFQ0105A'='SYMPTOMS'
'NFQ0105B'='SYMPTOMS'
'NFQ0105C'='SYMPTOMS'
'NFQ0105D'='SYMPTOMS'
'NFQ0105E'='SYMPTOMS'
'NFQ0106A'='SYMPTOMS'
'NFQ0106B'='SYMPTOMS'
'NFQ0106C'='SYMPTOMS'
'NFQ0106D'='SYMPTOMS'
'NFQ0106E'='SYMPTOMS'
'NFQ0107A'='SYMPTOMS'
'NFQ0107B'='SYMPTOMS'
'NFQ0107C'='SYMPTOMS'
'NFQ0107D'='SYMPTOMS'
'NFQ0107E'='SYMPTOMS'
'NFQ0108'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0109'='SYMPTOMS'
'NFQ0110'='SMALL FIBER NEUROPATHY'
'NFQ0111'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0112'='ACTIVITIES OF DAILY LIVING'
'NFQ0113'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0114'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0115'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0116'='SMALL FIBER NEUROPATHY'
'NFQ0117'='SMALL FIBER NEUROPATHY'
'NFQ0118'='SMALL FIBER NEUROPATHY'
'NFQ0119'='AUTONOMIC NEUROPATHY'
'NFQ0120'='AUTONOMIC NEUROPATHY'
'NFQ0121'='AUTONOMIC NEUROPATHY'
'NFQ0122'='ACTIVITIES OF DAILY LIVING'
'NFQ0123'='ACTIVITIES OF DAILY LIVING'
'NFQ0124'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0125'='ACTIVITIES OF DAILY LIVING'
'NFQ0126'='ACTIVITIES OF DAILY LIVING'
'NFQ0127'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0128'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0129'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0130'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0131'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0132'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0133'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0134'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
'NFQ0135'='PHYSICAL FUNCTIONING/LARGE FIBER NEUROPATHY'
;
    value $qsloc
    'NFQ0101A'='FOOT'
'NFQ0101B'='LEG'
'NFQ0101C'='HAND'
'NFQ0101D'='ARM'
'NFQ0102A'='FOOT'
'NFQ0102B'='LEG'
'NFQ0102C'='HAND'
'NFQ0102D'='ARM'
'NFQ0103A'='FOOT'
'NFQ0103B'='LEG'
'NFQ0103C'='HAND'
'NFQ0103D'='ARM'
'NFQ0104A'='FOOT'
'NFQ0104B'='LEG'
'NFQ0104C'='HAND'
'NFQ0104D'='ARM'
'NFQ0105A'='FOOT'
'NFQ0105B'='LEG'
'NFQ0105C'='HAND'
'NFQ0105D'='ARM'
'NFQ0106A'='FOOT'
'NFQ0106B'='LEG'
'NFQ0106C'='HAND'
'NFQ0106D'='ARM'
'NFQ0107A'='FOOT'
'NFQ0107B'='LEG'
'NFQ0107C'='HAND'
'NFQ0107D'='ARM'
'COM0106A'='HAND'
'COM0106B'='FOOT'
;
quit;



/*Step 3: Main body for SDTM derivation*/
data qs3; 
    set qs2; 
    studyid = _study; 
    domain = 'QS'; 
    usubjid = catx("/",STUDYID,_SUBJECT); 
    qstestcd = _qstestcd; 
    if qstestcd = "EQ5D206C" then qstestcd = "EQ5D0206";
    qstest = _qstest; 
    if qstestcd = "KPSS01" then do;
        qstestcd = "KPSS0101";
        qstest = "KPSS01-Karnofsky Performance Status";
    end;
/*     if qstestcd in ('COM0106A' 'COM0106B') then qstest = "Body Affected by Color Changes"; */
    qscat = _qscat; 
    if (qscat='OCULQCAT' and _oculqyn='C49487') or _module='REVPRDI'
        then do; 
        qsstat="NOT DONE";
        qstest="Questionnaires";
        qstestcd="QSALL";
    end;
    if qscat in ('KCCQ' 'Norfolk QoL-DN') then 
        qsscat=ifc(qstestcd="QSALL","",put(qstestcd,qsscat.));
    if _module = 'REVPRDI' then qsreasnd=ifc(_QSREASND eq '99' and _QREASNDO ne ' ', 
            upcase(_QREASNDO), upcase(putc(_QSREASND,vformat(_QSREASND))));
    if (qscat="Norfolk QoL-DN" and substr(qstestcd,8,1) in ('A' 'B' 'C' 'D'))
        or index(qstestcd,'COM0106')>0
        then qsloc=put(qstestcd,qsloc.);
    if qscat="EQ-5D-5L" then qsmethod=_qsmethod;
    qsorres=_qsorres;
    qsstresc=_qsstresc;
    qsstresn=_qsstresn;
    qseval=upcase(put(_qseval,$EVAL2F.));
    visitnum=_visit;
    %sdtm_dtc(invar_dat=_qsdat, invar_tim=_qstim, outvar_dtc=qsdtc);
    %sdtm_dy(invar_dtc=qsdtc, outvar_dy=qsdy);
    qsevintx=strip(_qscevint);
    module=_module;
    %sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
    if qscat='KPS SCALE' then do; qsmreas=_qsmreas; qsmoth=_qsmoth; end;
    if QSTESTCD="COM0117A" then cq17frq=ifc(^missing(_com0117B),strip(put(_com0117B,best.)),"");
    if QSTESTCD="COM0121A" then cq21frq=ifc(^missing(_com0121B),strip(put(_com0121B,best.)),"");
    if QSTESTCD="COM0124A" then cq24frq=ifc(^missing(_com0124B),strip(put(_com0124B,best.)),"");
    if QSTESTCD="COM0125A" then cq25frq=ifc(^missing(_com0125B),strip(put(_com0125B,best.)),"");
    if QSTESTCD="COM0126A" then cq26frq=ifc(^missing(_com0126B),strip(put(_com0126B,best.)),"");
run;


/* To derive EPOCH  */
 %sdtm_epoch(indata=qs3, outdata=qs4, domain= qs, debug=Y); 
    
/* To derive VISIT  */
 %sdtm_visit(indata = qs4, outdata=qs4); 
 
data _sv;
    set sdtm.sv;
    vv = visit;
    vn = visitnum;
    keep usubjid svstdtc vv vn;
    rename svstdtc=visitdtc;
    proc sort; by usubjid visitdtc;
run;

proc sort data=qs4; by usubjid visitdtc;
data qs5;
    merge qs4 (in=a) _sv;
    by usubjid visitdtc;
    if a;
    if missing(visit) and ^missing(vn) then do;
        visit = vv;
        visitnum = vn;
    end;
run;

  options mprint mlogic symbolgen;
/* To derive --SEQ  */
 %sdtm_seq(indata=qs5, domain=qs); 
    
  
/* To derive Baseline Flag for Findings Domains  */
 %sdtm_blfl(domain = qs, indata = qs5, outdata = qs6 , sortby=studyid usubjid &domain.testcd visitnum &domain.dtc , groupvar=&domain.testcd, debug = N); 
 %sdtm_lobxfl(domain = qs, indata = qs6, outdata = qs6 , sortby=studyid usubjid &domain.testcd visitnum &domain.dtc , groupvar=&domain.testcd, debug = N); 
  
  
/* Step 4: Create Main Domain Dataset */
/* ***final dataset****; */
%sdtm_rescrn(dsin=qs6, dsout=final_sdtm, debug=N);
  
 %let nobs=%count_obs(indata=final_sdtm); 
 %if &nobs ne 0 %then 
     %do; 
     ***final SDTM dataset****; 
     %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.);  
     %end; 

/* Step 5: Create Supp-- Dataset */
 %sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , 
            qeval_condi = if qorig="Assigned" then qeval = 'SPONSOR', debug=Y); 
  
/* ****Check and update if anything need manually update****; */
/* data final_supp; */
/*   set final_supp; */
/*   if qval = "." then delete; */
/* run; */

 %let nobs=%count_obs(indata=final_supp); 
 %if &nobs ne 0 %then 
     %do; 
     %let supplabel =  Supplemental Qualifiers for %sysfunc(upcase(&domain.)); 
     %put &supplabel; 
     ***final SUPP dataset****; 
     data sdtm.supp&pgmname.(label = "&supplabel."); 
       set final_supp; 
     run;   
     %end; 

/* **************************************************************************; */
/* * End of Programming */
/* **************************************************************************; */
%logcheck_indi;

