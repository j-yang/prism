**************************************************************************;
* Program name      : pr.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.pr
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-23
*
* Input datasets    : SDTM.DM, RAW.HISS, RAW.TISBIO, RAW.PR

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : pr.sas7bdat
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
option mprint;
*proc printto;
/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
%sdtm_initfmt(rawdata= tisbio pr hiss);


/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
	set hiss(where=(mhyn='Y')) PR(where=(pryn='Y')) tisbio;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/

data pr1;
	set pr0;
	studyid = 'D8450C00005';
	DOMAIN = 'PR';
	USUBJID = CATS(STUDYID,'/',_SUBJECT);
	module = _module;
	%sdtm_dtc(invar_dat=_vis_dat,outvar_dtc=visitdtc);
	visitnum = _visit;
	if _module = 'TISBIO' then do;
		prspid = compress(_MODULE||'-'||put(_LINE,z3.));
		prtrt = 'TISSUE BIOPSY';
		prcat = 'TISSUE BIOPSY TEST';
		prpresp = 'Y';
		proccur = substr(_biopyn,1,1);
		prloc = _bioptis;
		%sdtm_dtc(invar_dat=_biopdat,outvar_dtc=prstdtc);
		%sdtm_dtc(invar_dat=_biopdat,outvar_dtc=prendtc);
		prlocoth = _tisoth;
	end;

	if _module = 'HISS' THEN DO;
		PRTRT = upcase(strip(_mhterm));
		prdecod = _pt_name;
		prcat = 'GENERAL SURGICAL HISTORY';
		%sdtm_dtc(invar_dat=_vis_dat, outvar_dtc=prdtc);
		%sdtm_dtc(invar_dat=_mhstdat, outvar_dtc=prstdtc);
		meddrav = _meddra_v;
		prbodsys = _soc_name;
		prbdsycd = cats(_soc_code);
		prhlgt = _hlgtname;
		prhlgtcd = cats(_hlgtcode);
		prhlt = _hlt_name;
		prhltcd = cats(_hlt_code);
		prllt = _llt_name;
		prlltcd = cats(_llt_code);
		prptcd = cats(_pt_code);
		prsoc = _soc_name;
		prsoccd = cats(_soc_code);
	end;

	if _module = '1PR' then do;
		PRTRT = upcase(strip(_PRTRT));
		PRDECOD = _PT_NAME;
		PRINDC = _prindc;
%sdtm_dtc(invar_dat=_prstdat, outvar_dtc=prstdtc);
		prindcs = _prindcs;
		meddrav = _meddra_v;
		prbodsys = _soc_name;
		prbdsycd = cats(_soc_code);
		prhlgt = _hlgtname;
		prhlgtcd = cats(_hlgtcode);
		prhlt = _hlt_name;
		prhltcd = cats(_hlt_code);
		prllt = _llt_name;
		prlltcd = cats(_llt_code);
		prptcd = cats(_pt_code);
		prsoc = _soc_name;
		prsoccd = cats(_soc_code);
		praeno1 = _praeno1;
		prmhno1 = _prmhno1;
	end;
array 	temp prbdsycd prhltcd prhlgtcd prlltcd prptcd prsoccd;
	do over temp;
		if temp ='.' then temp = '';
	end;

run;



data pr;
	set pr1;
	%sdtm_dy(INVAR_DTC = &pgmname.dtc , OUTVAR_DY = &pgmname.dy );
	%sdtm_dy(INVAR_DTC = &pgmname.stdtc , OUTVAR_DY = &pgmname.stdy );
	%sdtm_dy(INVAR_DTC = &pgmname.endtc , OUTVAR_DY = &pgmname.endy );
run;
 
/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain., outdata=&domain., domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain., domain=&domain.);

/*To derive VISIT */ 
%sdtm_visit(indata = &domain., outdata=&domain.);


/*Step 4: Create Main Domain Dataset*/
***final dataset****;

%sdtm_rescrn(dsin=pr, dsout=final_sdtm, debug=N);
%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp, 
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

*proc compare data=sdtm.pr comp=qcsdtm.v_pr; 
*quit;
