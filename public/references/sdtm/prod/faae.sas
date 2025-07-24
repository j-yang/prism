**************************************************************************;
* Program name      : faae.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.faae
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.INJSTRC

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : faae.sas7bdat
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
options mprint; 
%sdtm_initfmt(rawdata=INJSTRC);

/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
	set injstrc;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/

data &pgmname.1;
	set &pgmname.0;
	STUDYID = 'D8450C00005';
	DOMAIN = 'FA';
	USUBJID = CAT(STUDYID,'/',_SUBJECT);
	FASPID = CAT(_MODULE,'-',_AENO);
	%sdtm_dtc(invar_dat=_vis_dat,outvar_dtc=fadtc);
	module = _module;
	%sdtm_dtc(invar_dat=_vis_dat,outvar_dtc=visitdtc);

	facat = 'INJECTION SITE REACTIONS';
	faobj = 'ONSET';
	FATESTCD = 'TIME';
	FATEST = 'Time';
	FAORRES = _ISRONTM;
	FASTRESC =CATS(_ISRONTM);
	output;

	faobj = 'RESOLUTION';
	FATESTCD = 'TIME';
	FATEST = 'Time';
	FAORRES = _ISRTIMRS;
	FASTRESC =CATS(_ISRTIMRS);
	output;
	
	FASCAT = 'SYMPTOMS';
	faobj = 'PRURITIS';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRPRUR;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'RASH';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRRASH;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'ERYTHEMA';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRERYT;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'SWELLING/EDEMA/INDURATION';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRWEDIN;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'PAIN/DISCOMFORT/TENDERNESS';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRPADTR;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'HEMATOMA AND BRUISING';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRHEBRU;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'BLEEDING';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRBLEED;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'WARMTH';
	FATESTCD = 'OCCUR';
	FATEST = 'Occurrence Indicator';
	FAORRES = _ISRWARM;
	FASTRESC =faorres;
	output;

	FASCAT = 'SYMPTOMS';
	faobj = 'WARMTH';
	FATESTCD = 'SPECIFY';
	FATEST = 'Specify';
	FAORRES = strip(upcase(_isroth));
	FASTRESC =faorres;
	output;

	FASCAT = 'SEVERITY';
	faobj = 'HIGHEST SEVERITY SYMPTOM';
	FATESTCD = 'SPECIFY';
	FATEST = 'Specify';
	FAORRES = _isrshsv;
	FASTRESC =faorres;
	output;

	FASCAT = 'SEVERITY';
	faobj = 'HIGHEST SEVERITY GRADE';
	FATESTCD = 'SEV';
	FATEST = 'Severity/Intensity';
	FAORRES = _isrhssg;
	FASTRESC = faorres;
	output;

	FASCAT = 'SEVERITY';
	faobj = 'HIGHEST SYMPTOM';
	FATESTCD = 'TIME';
	FATEST = 'Time';
	FAORRES = _isronths;
	FASTRESC = CATS(faorres);
	output;

/*	call missing(fascat);*/
/*	faobj = 'AFFECTED AREA';*/
/*	FATESTCD = 'DIAM';*/
/*	FATEST = 'Diameter';*/
/*	faorres = put(_isrdaa,best.);*/
/*	fastresc = faorres;*/
/*	faorresu = _isrdaau;*/
/*	fastresn = _isrdaa;*/
/*	fastresu = faorresu;*/
/*	output;*/
run;


/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain.1, outdata=&domain., domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain., domain=&domain.);

/*To derive VISIT */ 
%sdtm_visit(indata =&domain., outdata=&domain.);


/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm;
  set &DOMAIN.;
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
    %let supplabel =  Supplemental Qualifiers for %sysfunc(upcase(&domain.));
    %put &supplabel;
    ***final SUPP dataset****;
    data sdtm.supp&pgmname.(label = "&supplabel.");
      set final_supp;
    run;  
    %end;

/*Step 6: Assign minimal lengths to varibales */
%let mainnobs=%count_obs(final_sdtm);
%if &mainnobs ne 0 %then
    %do;
    %trimvarlen(dsin=sdtm.&pgmname.,dsout=sdtm.&pgmname.);; 
    %end;

%let suppnobs=%count_obs(final_supp);
%if &suppnobs ne 0 %then
    %do;
    %trimvarlen(dsin=sdtm.supp&pgmname.,dsout=sdtm.supp&pgmname.);; 
    %end;
/* **************************************************************************; */
/* * End of Programming */
/* **************************************************************************; */
%logcheck_indi;

