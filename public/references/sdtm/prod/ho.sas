**************************************************************************;
* Program name      : ho.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ho and sdtm.suppho
*
* Author            : Zifan Guo (knfg575)
*
* Date created      : 2024-01-15
*
* Input datasets    : sdtm.dm, raw.hosplog

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : sdtm.ho and sdtm.suppho
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

options mprint mlogic;
/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
    set raw.hosplog;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);

%macro generate_desc(num=,invar=,outvar=);
%do i=1 %to &num;
    %let j=%sysfunc(putn(&i.,z2.));
    %put &j;
    &outvar.&j.=&invar.&j.;
%end;
%mend;
/*Step 3: Main body for SDTM derivation*/
data &pgmname.1;
    set &pgmname.0;
    length hlreas $200.;
    studyid='D8450C00005';
    domain='HO';
    usubjid=catx('/',studyid,_subject);
    hospid=catx('-',_module,_aeno);
    holnkgrp=cats('AE-',_aeno);
    hoterm='HOSPITAL';
    if _hlreas='1' then hocat='HOSPITALIZATION, ELECTIVE';
    else if _hlreas='2' then hocat='HOSPITALIZATION, EVENT';
    visitnum=_visit;
    %sdtm_dtc(invar_dat=_hostdat, invar_tim=, outvar_dtc=hostdtc);
    %sdtm_dtc(invar_dat=_hoendat, invar_tim=, outvar_dtc=hoendtc);
    %sdtm_dy(invar_dtc=hostdtc, outvar_dy=hostdy);
    %sdtm_dy(invar_dtc=hoendtc, outvar_dy=hoendy);
    hlreas = putc(_HLREAS, vformat(_HLREAS));
    %generate_desc(num=10,invar=_evdesc,outvar=hodesc);
    module=_module;
    %sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
run;

/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);


 
/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain.1, outdata=&domain.2, domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain.2, domain=&domain.);

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

