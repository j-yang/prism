**************************************************************************;
* Program name      : vs.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.vs and sdtm.suppvs
*
* Author            : Zifan Guo (knfg575)
*
* Date created      : 2024-01-18
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_init, %sdtm_dtc, %sdtm_dy
*
* Output files      : sdtm.vs and sdtm.suppvs
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

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
/*%sdtm_initfmt(rawdata=);*/

options mlogic mprint;
/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
    set raw.vs;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/
data &pgmname.1;
    set &pgmname.0;
    studyid='D8450C00005';
    domain='VS';
    USUBJID = catx("/",STUDYID,_SUBJECT);
    vsspid=strip(put(_line,6.));
    put vsspid= _line=;
    visitnum=_visit;
    %sdtm_dtc(INVAR_DAT=_vsdat ,INVAR_TIM=_VSTIM ,OUTVAR_DTC=&pgmname.dtc )
    %sdtm_dtc(INVAR_DAT=_VIS_DAT ,INVAR_TIM= ,OUTVAR_DTC=visitdtc )
    MODULE = _MODULE;
    %sdtm_dy(INVAR_DTC = &pgmname.dtc , OUTVAR_DY = &pgmname.dy );
    if _VSPERF='C49488' then VSSTAT="";
    else if _VSPERF='C49487' then do;
    VSSTAT="NOT DONE";
    VSTESTCD = "VSALL";
    VSTEST = "Vital Signs";
    output;
    end;
    if not missing(_SBP) then do;
    vstestcd='SYSBP';
    VSTEST='Systolic Blood Pressure';
    VSCAT='PULSE AND BLOOD PRESSURE';
    VSORRES=strip(put(_SBP,best.));
    VSORRESU='mmHg';
    VSSTRESC=VSORRES;
    VSSTRESN=_SBP;
    VSSTRESU=VSORRESU;
    output;
    end;
    if not missing(_DBP) then do;
    vstestcd='DIABP';
    VSTEST='Diastolic Blood Pressure';
    VSCAT='PULSE AND BLOOD PRESSURE';
    VSORRES=strip(put(_DBP,best.));
    VSORRESU='mmHg';
    VSSTRESC=VSORRES;
    VSSTRESN=_DBP;
    VSSTRESU=VSORRESU;
    output;
    end;
    if not missing(_HRATE) then do;
    vstestcd='HR';
    VSTEST='Heart Rate';
    VSCAT='PULSE AND BLOOD PRESSURE';
    VSORRES=strip(put(_HRATE,best.));
    VSORRESU='beats/min';
    VSSTRESC=VSORRES;
    VSSTRESN=_HRATE;
    VSSTRESU=VSORRESU;
    output;
    end;
    if not missing(_RRATE) then do;
    vstestcd='RESP';
    VSTEST='Respiratory Rate';
    VSCAT='RESPIRATORY';
    VSORRES=strip(put(_RRATE,best.));
    VSORRESU='breaths/min';
    VSSTRESC=VSORRES;
    VSSTRESN=_RRATE;
    VSSTRESU=VSORRESU;
    output;
    end;
    if not missing(_TEMP) then do;
    vstestcd='TEMP';
    VSTEST='Temperature';
    VSCAT='BODY TEMPERATURE';
    VSORRES=strip(put(_TEMP,best.));
    VSORRESU='C';
    VSSTRESC=VSORRES;
    VSSTRESN=_TEMP;
    VSSTRESU=VSORRESU;
    output;
    end;
    if not missing(_WEIGHT) then do;
    vstestcd='WEIGHT';
    VSTEST='Weight';
    VSCAT='BODY MEASUREMENT';
    VSORRES=strip(put(_WEIGHT,best.));
    VSORRESU='kg';
    VSSTRESC=VSORRES;
    VSSTRESN=_WEIGHT;
    VSSTRESU=VSORRESU;
    output;
    end;
    if not missing(_HEIGHT) then do;
        vstestcd='HEIGHT';
        VSTEST='Height';
        VSCAT='BODY MEASUREMENT';
        VSORRES=strip(put(_HEIGHT,best.));
        VSORRESU='cm';
        VSSTRESC=VSORRES;
        VSSTRESN=_HEIGHT;
        VSSTRESU=VSORRESU;
        output;
    end;
run;

/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);
 
/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain.1, outdata=&domain.2, domain= &domain., debug=N);

options mlogic mprint symbolgen;
/*To derive --SEQ */ 
%sdtm_seq(indata=&domain.2, domain=&domain.);

/*To derive VISIT */ 
%sdtm_visit(indata = &domain.2, outdata=&domain.3);

/*To derive Baseline Flag for Findings Domains */ 
%sdtm_blfl(domain = &domain., indata = &domain.3, outdata = &domain.4 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);
%sdtm_lobxfl(domain = &domain., indata = &domain.4, outdata = &domain.5 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);


/*Step 4: Create Main Domain Dataset*/
***final dataset****;
%sdtm_rescrn(dsin=&domain.5, dsout=final_sdtm, debug=N);

/*%trimvarlen(dsin=final_sdtm, dsout=final_sdtm); */

%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , 
            qeval_condi = if qorig="Assigned" then qeval = 'SPONSOR', debug=Y);

****Check and update if anything need manually update****;
data final_supp;
  set final_supp;
run;

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

