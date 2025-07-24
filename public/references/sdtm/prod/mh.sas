**************************************************************************;
* Program name      : mh.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program/mh.sas
*
* Type              : SAS program
*
* Purpose           : To create sdtm.mh and sdtm.suppmh
*
* Author            : Zifan Guo (knfg575)
*
* Date created      : 2024-01-15
*
* Input datasets    : raw.mh, sdtm.dm

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : sdtm.mh, sdtm.suppmh
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
/*%sdtm_initfmt(rawdata=mh);*/

options mlogic mprint;
/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
    set raw.mh(where=(MHYN="C49488"));
run;
/*proc format cntlin=raw.cntlin;quit;*/
%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/
data &pgmname.1;
    set &pgmname.0;
    studyid="D8450C00005";
    domain='MH';
    USUBJID = catx("/",STUDYID,_SUBJECT);
    mhspid=strip(put(_line,best.));
    mhterm=upcase(strip(_mhterm));
    mhllt=_llt_name;
    mhlltcd=_llt_code;
    mhdecod=_pt_name;
    mhptcd=_pt_code;
    mhhlt=_hlt_name;
    mhhltcd=_hlt_code;
    mhhlgt=_hlgtname;
    mhhlgtcd=_hlgtcode;
    mhbodsys=_soc_name;
    mhbdsycd=_soc_code;
    mhsoc=_soc_name;
    mhsoccd=_soc_code;
    
    if _mhcurm='C49487' then mhcontrt='N';
    else if _mhcurm='C49488' then mhcontrt='Y';

    if _module="MH" then mhcat='MEDICAL HISTORY';
    else if _module ne "" then 
        do;
        title "Programming Notes:";
        file print;
        put _page_;
        put "Err" "or: module " _module " should be checked";
        end;
    
/*    if _module= "LIVERRF" then MHPRESP="Y";*/
    
    %sdtm_dtc(INVAR_DAT=_VIS_DAT ,INVAR_TIM= ,OUTVAR_DTC=&pgmname.dtc );
    %sdtm_dtc(INVAR_DAT=_MHSTDAT ,INVAR_TIM= ,OUTVAR_DTC=&pgmname.stdtc );
    %sdtm_dtc(INVAR_DAT=_MHENDAT ,INVAR_TIM= ,OUTVAR_DTC=&pgmname.ENDTC );
    
    
    if _module="MH" then
        do;
        if _MHONGO='C49487' then 
            do; 
            mhenrtpt='BEFORE';
            mhentpt=mhdtc;
            end;
        else if _MHONGO='C49488' then 
            do;
            mhenrtpt='ONGOING';
            mhentpt=mhdtc;
            end;
        else if _MHONGO ne "" then 
            do;
            title "Programming Notes:";
            file print;
            put _page_;
            put "Err" "or: MHONGO " _MHONGO " should be checked";
            end;
        end;
    module=_module;
    meddrav=_meddra_v;
    mhcurm=mhcontrt;
    visitnum=_visit;
    %sdtm_dtc(INVAR_DAT=_VIS_DAT ,INVAR_TIM= ,OUTVAR_DTC=visitdtc ); 
    %sdtm_dy(INVAR_DTC = &pgmname.dtc , OUTVAR_DY = &pgmname.dy );
    %sdtm_dy(INVAR_DTC = &pgmname.stdtc , OUTVAR_DY = &pgmname.stdy );
    %sdtm_dy(INVAR_DTC = &pgmname.endtc , OUTVAR_DY = &pgmname.endy );
    
run;

/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);


 
/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain.1, outdata=&domain.2, domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain.2, domain=&domain);

/*To derive VISIT */ 
%sdtm_visit(indata = &domain.2, outdata=&domain.3);

/*To derive Baseline Flag for Findings Domains */ 
/*%sdtm_blfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);*/
/*%sdtm_lobxfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);*/


/*Step 4: Create Main Domain Dataset*/
***final dataset****;
%sdtm_rescrn(dsin=&domain.3, dsout=final_sdtm, debug=N);

%trimvarlen(dsin=final_sdtm, dsout=final_sdtm); 

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

proc sort data=sdtm.mh; by STUDYID USUBJID MHCAT MHTERM MHDECOD MHSTDTC MHDTC MHSPID; run;
