**************************************************************************;
* Program name      : co.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.co
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.LIVERRF

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_initfmt, %sdtm_init, %logcheck_indi,
					  %sdtm_dtc, %sdtm_dy, %sdtm_seq, %sdtm_build, %sdtm_suppxx
*
* Output files      : co.sas7bdat
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
%sdtm_initfmt(rawdata=LIVERRF);


/*Step 2: Shell for SDTM derivation*/
%macro test
		(test=%str('ATTR Diagnosis'),testcd=%str('DIAGNOS'),cat=%str('Disease History'),scat=%str(''),
		obj=%str(''),res=%str(''),unit=%str(''),eval=%str(''),spfy=%str(''),where=%str()
		);
	%local domain;
	%let domain=fa;
	if &where. then do;
		&domain.test=&test.;
		&domain.testcd=&testcd.;
		&domain.cat=&cat.;
		&domain.scat=&scat.;
		&domain.obj=&obj.;
		&domain.orres=&res.;
		&domain.orresu=&unit.;
		&domain.eval=&eval.;
		&domain.spfy=&spfy.;
		
		output;
	end;
%mend test;

%put &domain.;
%macro sdtm_studyid;
	studyid='D8450C00005';
	usubjid=catx('/',studyid,_subject);
	domain="%upcase(&domain.)";

%mend sdtm_studyid;

*LIVERRF;
%sdtm_init(domain=&pgmname.,rawdata=LIVERRF,outdata=LIVERRF0I);

data _1z0&domain.0d;
	set LIVERRF0I;	
	*for CO ;
	%sdtm_studyid;
	idvar='FASEQ';
	coref='LIVER RISK FACTOR COMMENT';
	coeval='PRINCIPAL INVESTIGATOR';
	array cc $200 module  ;
	array cco _module ;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;

	*FOR LINK WITH FA;
	length facat fatest fatestcd faobj faspid $200.;
	faspid=strip(put(_MHCSPID,best.));
	
	%sdtm_dtc(invar_dat=_LIVDAT, invar_tim=, outvar_dtc=fadtc);

	%test(test=%str('Occurrence Indicator'),testcd=%str('OCCUR'),cat=%str('LIVER RISK FACTORS/LIFE STYLE EVENTS'),
		obj=%str(_LIVRF),res=%str(substr(_LIVRFOCC,1,1))
		,where=%str(_LIVRF ne ''));	
run;

proc sort data=_1z0&domain.0d;by usubjid facat faobj fatestcd fadtc faspid;run;
proc sort data=sdtm.fa out=mer0fa;by usubjid facat faobj fatestcd fadtc faspid;run;

data _1z0&domain.0d1;
	merge _1z0&domain.0d(in=a) mer0fa(keep=usubjid facat faobj fatestcd fadtc faspid faseq);
	by usubjid facat faobj fatestcd fadtc faspid;
	if a;
	idvarval=strip(put(faseq,best.));
	proc sort ;
	by usubjid idvar idvarval;
run;


data _z0&domain.0d;
	set _1z0&domain.0d1;
	array aa _LVRCOM1-_LVRCOM10;
	do i=1 to dim(aa);
		if aa(i) ne '' then do;
			coval=strip(upcase(aa(i)));
			output;
		end;
	end;

	proc sort ;
	by usubjid idvar idvarval coval;
run;



/*Step 3: Main body for SDTM derivation*/

data a0&domain.01;
	set _z0&domain.0:;

	proc sort ;
	by usubjid idvar idvarval coref  coval ;
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
data final_sdtm0;
	set a0&domain.01;
	drop _:;
run;

%sdtm_rescrn(dsin=final_sdtm0, dsout=final_sdtm, debug=Y);


%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , qeval_condi = %str(if qorig='Assigned' then qeval = 'SPONSOR'), debug=Y);

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

