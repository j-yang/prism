**************************************************************************;
* Program name      : ft.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ft
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : RAW.SIXMWT, RAW.LLFT, SDTM.DM

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : ft.sas7bdat, suppft.sas7bdat
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
%sdtm_initfmt(rawdata=LLFT SIXMWT);


/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
	set llft sixmwt;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/

data ft1;
	set ft0;
	studyid = 'D8450C00005';
	DOMAIN = 'FT';
	USUBJID = CATs(STUDYID,'/',_SUBJECT);
	module = _module;
	visitnum = _visit;
	FTSPID = cats(_line);
	%sdtm_dtc(invar_dat=_vis_dat,outvar_dtc=visitdtc);
	if module ='LLFT' then do;

		FTCAT = 'Lower Limb Function';
	
		if _llftyn = 'N' then do;
			ftstat = 'NOT DONE';
			FTTESTCD = 'FTALL';
			FTTEST = 'Functional Tests';
			OUTPUT;
		END;
		ELSE DO;
			%SDTM_DTC(invar_dat=_llftdat,outvar_dtc=ftdtc);
			fttest = 'Walk on Toes';
			fttestcd = 'FUNCTN1';
			ftorres = upcase(_llft0101);
			ftstresc = ftorres;
			ftdir = 'LOWER';
			ftloc = 'LIMB, LOWER';
			ftlat = 'RIGHT';
			OUTPUT;
		call missing(fttestcd,fttest,ftorres,
				ftstresc,ftdir,ftloc,ftlat);
			fttest = 'Walk on Toes';
			fttestcd = 'FUNCTN1';
			ftorres = upcase(_llft0102);
			ftstresc = ftorres;
			ftdir = 'LOWER';
			ftloc = 'LIMB, LOWER';
			ftlat = 'LEFT';
			OUTPUT;
		call missing(fttestcd,fttest,ftorres,
				ftstresc,ftdir,ftloc,ftlat);
			fttest = 'Walk on Heels';
			fttestcd = 'FUNCTN2';
			ftorres = upcase(_llft0103);
			ftstresc = ftorres;
			ftdir = 'LOWER';
			ftloc = 'LIMB, LOWER';
			ftlat = 'RIGHT';
			OUTPUT;
		call missing(fttestcd,fttest,ftorres,
				ftstresc,ftdir,ftloc,ftlat);
			fttest = 'Walk on Heels';
			fttestcd = 'FUNCTN2';
			ftorres = upcase(_llft0104);
			ftdir = 'LOWER';
			ftloc = 'LIMB, LOWER';
			ftlat = 'LEFT';
			ftstresc = ftorres;
			OUTPUT;
		call missing(fttestcd,fttest,ftorres,
				ftstresc,ftdir,ftloc,ftlat);

			fttest = 'Arise from Kneeled Position';
			fttestcd = 'FUNCTN3';
			ftorres = upcase(_llft0105);
			ftstresc = ftorres;
			ftdir = 'LOWER';
			ftloc = 'LIMB, LOWER';
			ftlat = 'RIGHT';
			OUTPUT;
		call missing(fttestcd,fttest,ftorres,
				ftstresc,ftdir,ftloc,ftlat);
			fttest = 'Arise from Kneeled Position';
			fttestcd = 'FUNCTN3';
			ftorres = upcase(_llft0106);
			ftstresc = ftorres;
			ftdir = 'LOWER';
			ftloc = 'LIMB, LOWER';
			ftlat = 'LEFT';
			OUTPUT;
		end;
	end;

	else if _module = 'SIXMWT' then do;
			call missing(fttestcd,fttest,ftcat,ftscat,ftorres,ftorresu,
				ftstresc,ftstresn,ftstresu,ftdir,ftloc,ftlat);
		ftcat = "SIX MINUTE WALK";

		if  _MWTYN = 'N' then do;
			ftstat = 'NOT DONE';
			fttest ='Functional Tests';
			fttestcd = 'FTALL';
			output;
		end;

		else if _MWTYN ='Y' then do;
				
			%sdtm_dtc(invar_dat=_mwtdat,outvar_dtc=ftdtc);
			fttestcd = 'STOP';
			fttest = 'Stopped or Paused Before 6 Minutes';
			ftorres = upcase(_mwtstyn);
			ftstresc = ftorres;
			output;
		call missing(fttestcd,fttest,ftorres,
				ftstresc);
			fttestcd = 'SUPPOT';
			fttest = 'Supplemental Oxygen During the Test';
			ftorres = upcase(_mwtsodt);
			ftstresc = ftorres;
			output;
		call missing(fttestcd,fttest,ftorres,
				ftstresc);
			fttestcd = 'SUPPOTF';
			fttest = 'Supplemental Oxygen Flow';
			ftorres = cats(_mwtflow);
			ftstresc = ftorres;
			ftstresn = _mwtflow;
			if not missing(ftorres) then  ftorresu = 'L/min';
			if not missing(ftorres) then  ftstresu = 'L/min';
			if _mwtsodt = 'Yes' then output;
		call missing(fttestcd,fttest,ftorres,ftorresu,
				ftstresc,ftstresn,ftstresu);
			fttestcd = 'SIXMW106';
			fttest = 'Total Dist Walked in 6 Min';
			ftorres = cats(_mwtTdw);
			ftstresc = ftorres;
			ftstresn = _mwtTdw;
			if not missing(ftorres) then ftorresu = 'm';
			if not missing(ftorres) then ftstresu = 'm';
			output;
		call missing(fttestcd,fttest,ftorres,ftorresu,
				ftstresc,ftstresn,ftstresu);
			fttpt = _mwttp1;
			fttestcd = 'HR';
			fttest = 'Heart Rate';
			ftorres = cats(_mwthr1);
			ftstresc = ftorres;
			ftstresn = _mwthr1;
			if not missing(ftorres) then  ftorresu = 'beats/min';
			if not missing(ftorres) then  ftstresu = 'beats/min';
			output;
		call missing(fttestcd,fttest,ftorres,ftorresu,
				ftstresc,ftstresn,ftstresu,fttpt
		);
			fttpt = _mwttp1;
			fttestcd = 'SPO2';
			fttest = 'SpO2';
			ftorres = cats(_mwtspo1);
			ftstresc = ftorres;
			ftstresn = _mwtspo1;
			if not missing(ftorres) then  ftorresu = '%';
			if not missing(ftorres) then  ftstresu = '%';
			output;
		call missing(fttestcd,fttest,ftorres,ftorresu,
				ftstresc,ftstresn,ftstresu,fttpt
		);
			fttpt = _mwttp1;
			fttestcd = 'DYSPNEA';
			fttest = 'Dyspnea';
			ftorres = upcase(_mwtdysp1);
			ftstresc = ftorres;
			ftstresn = input(ftstresc,??best.);
			output;		
		call missing(fttestcd,fttest,ftorres,
				ftstresc,fttpt
		);
			fttpt = _mwttp1;
			fttestcd = 'FATIGUE';
			fttest = 'Fatigue';
			ftorres = upcase(_mwtfatg1);
			ftstresc = ftorres;
			ftstresn = input(ftstresc,??best.);
			output;
		call missing(fttestcd,fttest,ftorres,
				ftstresc,fttpt
		);
			fttpt = _mwttp2;
			fttestcd = 'HR';
			fttest = 'Heart Rate';
			ftorres = cats(_mwthr2);
			ftstresc = ftorres;
			ftstresn = _mwthr2;
			if not missing(ftorres) then ftorresu = 'beats/min';
			if not missing(ftorres) then ftstresu = 'beats/min';
			output;
		call missing(fttestcd,fttest,ftorres,ftorresu,
				ftstresc,ftstresn,ftstresu,fttpt
		);	
			fttpt = _mwttp2;
			fttestcd = 'SPO2';
			fttest = 'SpO2';
			ftorres = cats(_mwtspo2);
			ftstresc = ftorres;
			ftstresn = _mwtspo2;
			if not missing(ftorres) then ftorresu = '%';
			if not missing(ftorres) then ftstresu = '%';
			output;

		call missing(fttestcd,fttest,ftorres,ftorresu,
				ftstresc,ftstresn,ftstresu,fttpt
		);
			fttpt = _mwttp2;
			fttestcd = 'DYSPNEA';
			fttest = 'Dyspnea';
			ftorres = upcase(_mwtdysp2);
			ftstresc = ftorres;
			ftstresn = input(ftstresc,??best.);
			output;	
	
		call missing(fttestcd,fttest,ftorres,
				ftstresc,fttpt
		);
			fttpt = _mwttp2;
			fttestcd = 'FATIGUE';
			fttest = 'Fatigue';
			ftorres = upcase(_mwtfatg2);
			ftstresc = ftorres;
			ftstresn = input(ftstresc,??best.);
			output;
		end;
	end;
run;

data ft2;
	set ft1;
	%sdtm_dy(invar_dtc=ftdtc,outvar_dy=ftdy);
	if fttpt = 'Pre-Test' then fttptnum = 1;
	else if fttpt = 'End-Test' then fttptnum = 2;
	mwtyspec = _mwtyspec;
	mwtadyn = upcase(_mwtadyn);
	adyspec = _adyspec;
	if ftorres = '.' then call missing(ftorres);
	if ftstresc = '.' then call missing(ftstresc);
	if missing(ftorres) then call missing(ftorresu,ftstresu);
	if fttestcd ne 'STOP' then call missing(MWTYSPEC);
run;


/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain.2, outdata=&domain., domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain., domain=&domain.);

/*To derive VISIT */ 
%sdtm_visit(indata = &domain., outdata=&domain.);

/*To derive Baseline Flag for Findings Domains */ 
%sdtm_blfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd ftlat ftdir &domain.dtc fttpt, groupvar=&domain.testcd ftlat ftdir fttpt, debug = N);
%sdtm_lobxfl(domain = &domain., indata = &domain., outdata = &domain. , sortby=studyid usubjid &domain.testcd ftlat ftdir &domain.dtc fttpt, groupvar=&domain.testcd ftlat ftdir fttpt, debug = N);


/*Step 4: Create Main Domain Dataset*/
***final dataset****;

%sdtm_rescrn(dsin=&domain., dsout=final_sdtm, debug=N);

%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
	%trimvarlen(dsin=sdtm.&domain.,dsout=sdtm.&domain.);
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , qeval_condi = if qorig="Assigned" then qeval = 'SPONSOR' , debug=Y);

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
	%trimvarlen(dsin=sdtm.supp&domain.,dsout=sdtm.supp&domain.);
    %end;

/* **************************************************************************; */
/* * End of Programming */
/* **************************************************************************; */
%logcheck_indi;

