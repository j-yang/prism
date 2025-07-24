**************************************************************************;
* Program name      : dv.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.dv and sdtm.suppdv
*
* Author            : Zifan Guo (knfg575)
*
* Date created      : 2024-01-30
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : sdtm.dv and sdtm.suppdv
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
proc printto;
/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
/*%sdtm_initfmt(rawdata=);*/

/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
    set raw.dv;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);
options mprint mlogic;
/*Step 3: Main body for SDTM derivation*/
data &pgmname.1;
    set &pgmname.0;
    studyid='D8450C00005';
    domain='DV';
    usubjid=catx('/',studyid,_subject);
    dvspid=_dvdecod;
    dvterm=_dvterm;
    dvdecod=_dvdecod;
    dvcat=upcase(_dvcat);
    dvscat=upcase(_dvscat);
    %sdtm_dtc(invar_dat=_dvdat, invar_tim=, outvar_dtc=dvdtc);
    %sdtm_dtc(invar_dat=_dvstdat, invar_tim=, outvar_dtc=dvstdtc);
    %sdtm_dy(invar_dtc=dvdtc, OUTVAR_DY = &pgmname.dy);
    %sdtm_dy(invar_dtc=dvstdtc, OUTVAR_DY = &pgmname.stdy);
    dvterm2=_dvterm2;
    dvterm3=_dvterm3;
    dvterm4=_dvterm4;
    dvterm5=_dvterm5;
    dvterm6=_dvterm6;
    dvterm7=_dvterm7; 
/*  dvterm8=_dvterm8; */
/*  dvterm9=_dvterm9; */
run;

/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);


 
/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain.1, outdata=&domain.2, domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain.2, domain=&domain.);

/*To derive VISIT */ 
/*%sdtm_visit(indata = _syslast_, outdata=&domain.);*/

/*To derive Baseline Flag for Findings Domains */ 
/*%sdtm_blfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);*/
/*%sdtm_lobxfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);*/


/*Step 4: Create Main Domain Dataset*/
***final dataset****;
%sdtm_rescrn(dsin=&domain.2, dsout=final_sdtm, debug=N);

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
