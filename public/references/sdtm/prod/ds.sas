**************************************************************************;
* Program name      : ds.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ds
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.CONSENT, RAW.CONSWD, RAW.DS, RAW.IE

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_initfmt, %sdtm_init, %logcheck_indi,
					  %sdtm_dtc, %sdtm_dy, %sdtm_visit, %sdtm_epoch, %sdtm_seq, %sdtm_build, %sdtm_suppxx
*
* Output files      : ds.sas7bdat
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
proc format cntlin=raw.cntlin;quit;

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
%sdtm_initfmt(rawdata=CONSENT IE DOSDISC DS CONSWD);

proc format ;
	value $dosdisc_decod
		'Subject decision' = 'WITHDRAWAL BY SUBJECT'
		'Adverse Event' = 'ADVERSE EVENT'
		'Severe non-compliance to protocol' = 'PROTOCOL DEVIATION'
		'Subject lost to follow-up' = 'LOST TO FOLLOW-UP'
		'Investigator decision' = 'PHYSICIAN DECISION'
		'Pregnancy' = 'PREGNANCY'
		'Study terminated by sponsor' = 'STUDY TERMINATED BY SPONSOR'
		'Death' = 'DEATH'
		'Consent withdrawal' = 'WITHDRAWAL OF CONSENT'
		'Other' = 'OTHER'
		'Condition under investigation worsened'='PROGRESSIVE DISEASE'
;
run;

/*Step 2: Shell for SDTM derivation*/
*CONSENT;
%sdtm_init(domain=&pgmname.,rawdata=consent,outdata=consent0i);
data _z0&domain.0a;
	set consent0i;
	if _dsaspid>. then &domain.spid=strip(put(_dsaspid,??best.));
	dsterm=upcase(_dsterm0);
	if _module='CONSENT' then dsdecod='INFORMED CONSENT OBTAINED';
	else if _module='CONSENT1' then dsdecod='INFORMED CONSENT OBTAINED';
	else if _module='CONSENT2' then dsdecod='INFORMED CONSENT OBTAINED';
	dscat='PROTOCOL MILESTONE';
	dsscat='';
	
	%sdtm_dtc(invar_dat=_dsstdat0, invar_tim=, outvar_dtc=dsstdtc);
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=dsdtc);

	array cc $200 module ;
	array cco  _module ;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;
run;



*IE;
%sdtm_init(domain=&pgmname.,rawdata=ie,outdata=ie0i);

data _z0&domain.0b;
	set ie0i;
	where substr(upcase(_DSCTERM),1,1)='Y' and _module='IE1';
	&domain.refid=strip(put(_patient,best.));
	dsterm='RANDOMIZED';
	dsdecod='RANDOMIZED';
	dscat='PROTOCOL MILESTONE';
	dsscat='';
	
	%sdtm_dtc(invar_dat=_DSCSTDAT, invar_tim=_DSCSTTIM, outvar_dtc=dsstdtc);
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=dsdtc);

	array cc $200 module ;
	array cco  _module ;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;
run;

data _z0&domain.0b1;
	set ie0i;
	where _ieyn IN ('Yes' 'Y');
	dsterm='ELIGIBILITY CRITERIA MET';
	dsdecod='ELIGIBILITY CRITERIA MET';
	dscat='PROTOCOL MILESTONE';
	dsscat='';
	
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=dsstdtc);
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=dsdtc);

	array cc $200 module ;
	array cco  _module ;

	do i=1 to dim(cc);
		cc(i)=cco(i);
	end;
run;

*DOSDISC;
%sdtm_init(domain=&pgmname.,rawdata=dosdisc,outdata=dosdisc0i);

data _z0&domain.0c;
	set dosdisc0i;
	where _ip_disc in ('Yes' 'Y');
	if _ipdcreas='Subject decision' then dsterm=strip(upcase(_ipdcsjds));
	else dsterm=strip(upcase(_ipdcreas));
	dsdecod=put(_ipdcreas,$dosdisc_decod.);;
	dscat='DISPOSITION EVENT';
	dsscat='STUDY TREATMENT';
	
	%sdtm_dtc(invar_dat=_ipdc_dat, invar_tim=, outvar_dtc=dsstdtc);
	%sdtm_dtc(invar_dat=_ipdcddat, invar_tim=, outvar_dtc=ipdcddat);

	array cc $200 module ipdcdspc ipdcspec;
	array cco  _module _ipdcdspc _ipdcspec;

	do i=1 to dim(cc);
		cc(i)=upcase(cco(i));
	end;
run;

*DS;
%sdtm_init(domain=&pgmname.,rawdata=ds,outdata=ds0i);

data _z0&domain.0d;
	set ds0i;
	where _dsdecod>'';
	if _dsterm >'' then dsterm= strip(upcase(_dsterm));
	else dsterm=strip(upcase(_dsdecod));
	dsdecod=strip(upcase(_dsdecod));
	dscat='DISPOSITION EVENT';
	dsscat='STUDY PARTICIPATION';
	
	%sdtm_dtc(invar_dat=_dsstdat, invar_tim=, outvar_dtc=dsstdtc);

	array cc $200 module dsspreli ;
	array cco  _module _dsspreli ;

	do i=1 to dim(cc);
		cc(i)=strip(cco(i));
	end;
run;

*CONSWD;
%sdtm_init(domain=&pgmname.,rawdata=conswd,outdata=conswd0i);

data _z0&domain.0e;
	length dsterm $200.;
	set conswd0i;
	where _dstdat13>'' and _oconwd in ('Yes' 'Y');
	dsterm=strip(upcase(_DSWDECOD));
	dsdecod='WITHDRAWAL OF CONSENT';
	dscat='DISPOSITION EVENT';
	dsscat='STUDY PARTICIPATION';
	
	%sdtm_dtc(invar_dat=_dstdat13, invar_tim=, outvar_dtc=dsstdtc);
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=dsdtc);

	array cc $200 module  ;
	array cco  _module  ;

	do i=1 to dim(cc);
		cc(i)=strip(cco(i));
	end;
run;

%macro sdtm_studyid;
	studyid='D8450C00005';
	usubjid=catx('/',studyid,_subject);
	domain="%upcase(&domain.)";

%mend sdtm_studyid;


/*Step 3: Main body for SDTM derivation*/
data a0&domain.01;
	set _z0&domain.0:;
	%sdtm_studyid;
	%sdtm_dy(invar_dtc=&domain.stdtc,outvar_dy=&domain.stdy);
	%sdtm_dy(invar_dtc=&domain.dtc,outvar_dy=&domain.dy);
	visitnum=_visit;
	proc sort ;
	by usubjid &domain.cat &domain.term &domain.stdtc;
run;



/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);


/*To derive VISIT */ 
%sdtm_visit(indata = a0&domain.01, outdata=a0&domain.91);

/*To derive EPOCH */ 
%sdtm_epoch(indata = a0&domain.91, outdata=a0&domain.92, domain= &domain., debug=N);

/*To derive Baseline Flag for Findings Domains */ 
*%sdtm_blfl(domain = &domain., indata = a0&domain.92, outdata = a0&domain.93 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);
*%sdtm_lobxfl(domain = &domain., indata = a0&domain.93, outdata = a0&domain.94 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);

/*To derive --SEQ */ 
%sdtm_seq(indata=a0&domain.92, domain=&domain.);


/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm0;
	set a0&domain.92;
	if module ='DOSDISC' and _studyper='Double Blind Treatment Period' then epoch='BLINDED TREATMENT';
	else if module='DOSDISC' and _studyper='Open Label Treatment Period' then epoch='OPEN LABEL TREATMENT';
	
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

