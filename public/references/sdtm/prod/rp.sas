**************************************************************************;
* Program name      : rp.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.rp
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : rp.sas7bdat
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
%*sdtm_initfmt(rawdata=);


/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
    set raw.PREGREP
      ;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);

/*Step 3: Main body for SDTM derivation*/

data &pgmname.1;
  set &pgmname.0;
  if not missing(_prothnx) then
  do;
    rporres=STRIP(PUT(_PROTHNX,BEST.));
    rpscat='PREVIOUS PREGNANCIES';
    rpstresc=STRIP(PUT(_PROTHNX,BEST.));
    rpstresn=_prothnx;
    rptest='Number of Other Previous Pregnancies';
    rptestcd='PROTHNX';
    PROTH=_s_proth;
    output;
  end;
run;

data &pgmname.2;
  set &pgmname.0;
  if not missing(_prcntr) then
  do;
    rporres=substr(vvalue(_PRCNTR),1,1);
    rpscat='CURRENT PREGNANCY';
    rpstresc=rporres;
    rptest='Using Hormonal Contraception or IUD';
    rptestcd='PRCNTR';
    PRCNTR=_s_prcntr;
    output;
  end;
run;

data &pgmname.3;
  set &pgmname.0;
  if not missing( _prsmnx) then
  do;
    rporres=STRIP(PUT(_PRSMNX, BEST.));
    rpscat='PREVIOUS PREGNANCIES';
    rpstresc=STRIP(PUT(_PRSMNX, BEST.));
    rpstresn=_prsmnx;
    rptest='Number of Spontaneous Abortions';
    rptestcd='SPABORTN';
    output;
  end;
run;

data &pgmname.4;
  set &pgmname.0;
  if not missing( _provnx) then
  do;
    rporres=STRIP(PUT(_PROVNX,BEST.));
    rpscat='PREVIOUS PREGNANCIES';
    rpstresc=STRIP(PUT(_PROVNX,BEST.));
    rpstresn=_provnx;
    rptest='Number of Previous Pregnancies';
    rptestcd='PRVPREGN';
    output;
  end;
run;

data &pgmname.5;
  set &pgmname.0;
  if not missing(_prndnx) then
  do;
    rporres=STRIP(PUT(_PRNDNX,BEST.));
    rpscat='PREVIOUS PREGNANCIES';
    rpstresc=STRIP(PUT(_PRNDNX,BEST.));
    rpstresn=_prndnx;
    rptest='Number of Normal Deliveries';
    rptestcd='PRNDNX';
    output;
  end;
run;

data &pgmname.6;
  set &pgmname.0;
  if not missing( _prrisk) then
  do;
    rporres=_prrisk;
    rpscat='RISK FACTOR';
    rpstresc=_prrisk;
    rptest='Relevant Pregnancy Risk Factor';
    rptestcd='PRRISK';
    output;
  end;
run;

data &pgmname.7;
  set &pgmname.0;
  if not missing( _prfamhis) then
  do;
    rporres=_prfamhis;
    rpscat='FAMILY HISTORY';
    rpstresc=_prfamhis;
    rptest='Relevant Family History';
    rptestcd='PRFAMHIS';
    output;
  end;
run;

data &pgmname.8;
  set &pgmname.0;
  if not missing( _prmp_dat) then
  do;
    rporres=_prmp_dat;
    rpscat='CURRENT PREGNANCY';
    rpstresc=_prmp_dat;
    rptest='Last Menstrual Period Start Date';
    rptestcd='LMPSTDTC';
    output;
  end;
run;

data &pgmname.9;
  set &pgmname.0;
  if not missing( _pred_dat) then
  do;
    rporres=_pred_dat;
    rpscat='CURRENT PREGNANCY';
    rpstresc=_pred_dat;
    rptest='Estimated Date of Delivery';
    rptestcd='EDLVRDTC';
    output;
  end;
run;

data &pgmname.10;
  set &pgmname.1 - &pgmname.9;
run;

data &pgmname.11;
  set &pgmname.10;
  domain='RP';
  rpcat='PREGNANCY REPORT';
  %sdtm_dtc(INVAR_DAT=_asm_dat ,INVAR_TIM= ,OUTVAR_DTC=&pgmname.dtc );
  studyid=_study;
  usubjid=cat( _study,  '/',   _subject);
  module=_module;
  
  %sdtm_dy(INVAR_DTC = &pgmname.dtc , OUTVAR_DY = &pgmname.dy );
run;


/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain.11, outdata=&domain., domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain., domain=&domain.);


/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm;
  set &domain.;
run;

%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , qeval_condi = , debug=Y);

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

