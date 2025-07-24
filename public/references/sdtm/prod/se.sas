**************************************************************************;
* Program name      : se.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.se
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : se.sas7bdat
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
*proc printto;
/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
%*sdtm_initfmt(rawdata=ec ds);

/*Step 2: Shell for SDTM derivation*/
proc format cntlin=raw.cntlin; quit;
data sdtm_dm;
  set sdtm.dm;
run;

data &pgmname._raw;
  set raw.visit;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);

/*Step 3: Main body for SDTM derivation*/

*Merge RFSTDTC from dm;
proc sql noprint;
	create table &pgmname.1 as
	select 	t1.*, 
			t2.RFICDTC,
			t2.RFSTDTC,
			t2.RFPENDTC,
			t2.ACTARMCD,
			t2.ARMNRS
	from &pgmname.0 as t1
	left join
	sdtm_dm as t2
	on strip(t1._SUBJECT) = t2.SUBJID;
quit;

data se1;
	set se1(rename=(_subject = in_subject));
	length _subject $200.;
	_subject = in_subject;
run;

data oledose;
	set raw.ec;
	length _subject $200.;
	where studyper = 'C102256' and ecyn = 'C49488';
	_subject = subject;
	%sdtm_dtc(invar_dat=ecstdat,invar_tim=ecsttim,outvar_dtc=oledosedtc);
	keep _subject oledosedtc;
proc sort ; by _subject oledosedtc;
proc sort nodupkey; by _subject;
run;


proc sql noprint;
	create table visit24 as
	select distinct subject as _subject length = 200, 
			max(vis_dat) as visit24
	from raw.visit
	where visit = 9
	group by subject
	order by subject
;quit;


proc sql noprint;
	create table visit104 as
	select distinct subject as _subject length = 200, 
			max(vis_dat) as visit104
	from raw.visit
	where visit = 29
	group by subject
	order by subject
;quit;

proc sql noprint;
	create table dsdat as
	select distinct subject as _subject length = 200, 
			max(dsstdat) as dsdat
	from raw.ds
	where not missing(dsdecod)
	group by subject
	order by subject
;quit;



data &pgmname.20;
  merge &pgmname.1 oledose visit104 dsdat;
  by _subject;
  studyid ='D8450C00005';
  domain ='SE';
  usubjid=strip(studyid)||"/"||strip(_subject);
proc sort; by usubjid;
run;

data _m_rescrn;
    set raw.consent;
    where module = 'CONSENT1' and not missing(dsstdat0);
    length usubjid $30.;
    label usubjid = '';
    usubjid = study||'/'||subject;
    rescrndat = dsstdat0;
keep usubjid rescrndat;
proc sort; by usubjid;
;run;

data &pgmname.2;
	merge &pgmname.20(in=a) _m_rescrn;
	by usubjid;
	if a;
run;

data &pgmname.3;
	set &pgmname.2;

  if RFICDTC ne '' then do;
    ETCD = 'SCRN';
	ELEMENT = 'Screening';
	EPOCH = 'SCREENING';
	TAETORD = 1;
	SESTDTC = coalescec(rescrndat,RFICDTC);
	seendtc = rfstdtc;
  output;
  end;

  if RFSTDTC ne '' and actarmcd ='E-E' then do;
    ETCD = 'DBE';
	ELEMENT = 'Eplontersen';
	EPOCH = 'BLINDED TREATMENT';
	TAETORD = 2;
	SESTDTC = RFSTDTC;
	seendtc = oledosedtc;
  output;
  end;

  if RFSTDTC ne ''  and actarmcd ='P-E' then do;
    ETCD = 'DBP';
	ELEMENT = 'Placebo';
	EPOCH = 'BLINDED TREATMENT';
	TAETORD = 2;
	SESTDTC = RFSTDTC;
	seendtc = oledosedtc;
  output;
  end;

  if not missing(oledosedtc) then do;
    ETCD = 'OE';
	ELEMENT = 'Open Label Eplontersen';
	EPOCH = 'OPEN LABEL TREATMENT';
	TAETORD = 3;
	SESTDTC = oledosedtc;
	seendtc = put(min(input(visit104,yymmdd10.),
					input(dsdat,yymmdd10.),
				input(rfpendtc,yymmdd10.)),yymmdd10.);
  output;
  end;

  if visit104 ne '' and rfpendtc >: visit104  then do;
    ETCD = 'FUP';
	ELEMENT = 'Follow-Up';
	EPOCH = 'FOLLOW-UP';
	TAETORD = 4;
	SESTDTC = visit104;
	SEENDTC = RFPENDTC;

  output;
  END; 
run;

proc sort data=	&pgmname.3 ;
  by usubjid etcd sestdtc SEENDTC;
run;

data &pgmname.3 ;
  set &pgmname.3 ;
  by usubjid etcd sestdtc SEENDTC;
  if first.etcd;
  if not missing(sestdtc) and missing(seendtc) then seendtc = rfpendtc;
run;

data &pgmname.3 ;
  set &pgmname.3 ;
  if sestdtc ne '';
 	%sdtm_dy(INVAR_DTC = &pgmname.stdtc , OUTVAR_DY = &pgmname.stdy );
 	%sdtm_dy(INVAR_DTC = &pgmname.endtc , OUTVAR_DY = &pgmname.endy );
run;
		
/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);

%*sdtm_visit(indata = _syslast_, outdata=&domain.);
%*sdtm_epoch(indata=&domain., outdata=&domain., domain= &domain., debug=N);
%sdtm_seq(indata=&pgmname.3,domain=&domain.);
%*sdtm_blfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);
%*sdtm_lobxfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);


/*Step 4: Assign attributes to dataset and variables*/
***final dataset****;
data final_sdtm;
  set _last_;
run;

%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&domain.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

*** get supp related records*****;
%*sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , qeval_condi = , debug=Y);

****Check and update if anything need manually update****;
/*data final_supp;*/
/*  set final_supp;*/
/*run;*/
/**/
/*%let nobs=%count_obs(indata=final_supp);*/
/*%if &nobs ne 0 %then*/
/*    %do;*/
/*    %let supplabel =  Supplemental Qualifiers for %sysfunc(upcase(&pgmname));*/
/*    %put &supplabel;*/
/*    ***final SUPP dataset****;*/
/*    data sdtm.supp&pgmname.(label = "&supplabel.");*/
/*      set final_supp;*/
/*    run;  */
/*    %end;*/

/* **************************************************************************; */
/* * End of Programming */
/* **************************************************************************; */
%logcheck_indi;

proc sort nodupkey dupout=test1 data=se1; by _subject; run;
proc sort nodupkey dupout=test2 data=oledose; by _subject; run;
proc sort nodupkey dupout=test3 data=visit104; by _subject; run;
proc sort nodupkey dupout=test4 data=dsdat; by _subject; run;
