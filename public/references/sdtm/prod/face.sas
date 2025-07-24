**************************************************************************;
* Program name      : face.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.face
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.DEATHEVT

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_initfmt, %sdtm_init, %logcheck_indi,
					  %sdtm_dtc, %sdtm_dy, %sdtm_seq, %sdtm_build, %sdtm_suppxx
*
* Output files      : face.sas7bdat
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
%let domain=FA;
%procprint_indi;

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
%sdtm_initfmt(rawdata=DEATHEVT);


/*Step 2: Shell for SDTM derivation*/
%sdtm_init(domain=&pgmname.,rawdata=DEATHEVT,outdata=DEATHEVT0i);

%macro test
		(test=%str(''),testcd=%str(''),cat=%str('DEATH EVENT'),
		obj=%str(_CETERM),res=%str(''),sires=%str('')
		);
	&domain.test=&test.;
	&domain.testcd=&testcd.;
	&domain.cat=&cat.;
	&domain.obj=&obj.;
	&domain.orres=&res.;
	&domain.stresc=&sires.;
	
	output;
%mend test;

data _z0&domain.0a;
	length module $200.;
	set DEATHEVT0i;
	
	module=strip(_module);
	&domain.lnkid=strip(module)||'-'||strip(put(_aeno,best.));
	&domain.lnkgrp='AE-'||strip(put(_aeno,best.));
	if _HOSPEV ne '' then do;
		%test(test=%str('Event Associated with Hospitalization'),testcd=%str('HOSPEV'),
			res=%str(_HOSPEV),sires=%str(_HOSPEV)
			);
	end;
	if _VASSCLS ne '' then do;
		%test(test=%str('Primary Cause of Death'),testcd=%str('PRCDTH'),
			res=%str(ifc(_vassclso ne '', trim(left(upcase(_vassclso))), upcase(_vasscls))),
			sires=%str(upcase(_vasscls))
			);
	end;
	if _NVASSCLS ne '' then do;
		%test(test=%str('Primary Cause of Death'),testcd=%str('PRCDTH'),
			res=%str(ifc(_nvassclo ne '', trim(left(upcase(_nvassclo))), upcase(_nvasscls))),
			sires=%str(upcase(_nvasscls))
			);
	end;
	
run;

/*Step 3: Main body for SDTM derivation*/


%macro sdtm_studyid;
	studyid='D8450C00005';
	usubjid=catx('/',studyid,_subject);
	domain="%upcase(&domain.)";

%mend sdtm_studyid;

data a0&domain.01;
	set _z0&domain.0:;
	%sdtm_studyid;
	visitnum=.;
	visit='';
	visitdtc='';
	proc sort ;
	by usubjid &domain.test ;
run;




/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);



/*To derive VISIT */ 
*%sdtm_visit(indata = a0&domain.01, outdata=a0&domain.91);

/*To derive EPOCH */ 
*%sdtm_epoch(indata = a0&domain.91, outdata=a0&domain.92, domain= &domain., debug=N);

/*To derive Baseline Flag for Findings Domains */ 
*%sdtm_blfl(domain = &domain., indata = a0&domain.92, outdata = a0&domain.93 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);
*%sdtm_lobxfl(domain = &domain., indata = a0&domain.93, outdata = a0&domain.94 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);

/*To derive --SEQ */ 
%sdtm_seq(indata=a0&domain.01, domain=&domain.);

/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm;
	set a0&domain.01;
	drop _:;
run;

%let nobs=%count_obs(final_sdtm);
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

%let nobs=%count_obs(final_supp);
%if &nobs ne 0 %then
    %do;
    %let supplabel =  Supplemental Qualifiers for %sysfunc(upcase(&pgmname.));
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

