**************************************************************************;
* Program name      : dd.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.dd and sdtm.suppdd
*
* Author            : Zifan Guo (knfg575)
*
* Date created      : 2024-01-17
*
* Input datasets    : SDTM.DM, RAW.SERAE                

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : sdtm.dd and sdtm.suppdd
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


/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
    set raw.serae (where=(aesdth='C49488' and ^missing(AESAUTOP)));
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/
data &pgmname.1;
    set &pgmname.0;
    studyid='D8450C00005';
    domain='DD';
    USUBJID = catx("/",STUDYID,_SUBJECT);
    ddspid='AE-'||strip(put(_AENO,best.));
    ddtestcd='AUTOPIND';
    ddtest='Autopsy Indicator';
    ddorres=putc(_aesautop,vformat(_aesautop));
    call missing(dddtc);
    ddstresc=ddorres;
    module=_module;
run;

/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);


 
/*To derive EPOCH */ 
/*%sdtm_epoch(indata=&domain., outdata=&domain., domain= &domain., debug=N);*/

/*To derive --SEQ */ 
%sdtm_seq(indata=&pgmname.1, domain=&domain.);

/*To derive VISIT */ 
/*%sdtm_visit(indata = _syslast_, outdata=&domain.);*/

/*To derive Baseline Flag for Findings Domains */ 
/*%sdtm_blfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);*/
/*%sdtm_lobxfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);*/


/*Step 4: Create Main Domain Dataset*/
***final dataset****;
%sdtm_rescrn(dsin=&pgmname.1, dsout=final_sdtm, debug=N);

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

