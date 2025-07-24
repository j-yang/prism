**************************************************************************;
* Program name      : pc.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.pc
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-07-16
*
* Input datasets    : sdtm.dm, dummy_pk

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : pc.sas7bdat
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


/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
	set raw.dummy_pk;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.01);


/*Step 3: Main body for SDTM derivation*/

data &pgmname.02;
	set &pgmname.01;
	length  pcrescom $200.;
	pcrefid=strip(_specid);
	pcspid=strip(put(_line,best.));
	if _visit>. then pcgrpid='VISIT '||strip(put(_visit,best.))||" DOSE";
	pctestcd='EPLO';
	pctest=strip(_analyte);
	pccat='ANALYTE';
	pcscat=strip(_speccat);
	pcorres=strip(_anaconc);
	if pcorres ne '' then pcorresu=strip(_anaconcu);

	if compress(compress(pcorres,'.','d'))='' then _res=input(pcorres,best.);
	if pcorresu='nM' and _res>. then pcstresc=strip(put(_res *8606.4992/1000,best.));
	else if pcorresu='ng/mL' and _res>. then pcstresc=strip(put(_res *1,best.));
	else if _res=. then pcstresc=pcorres;
	pcstresn=input(pcstresc,??best.);
	if pcstresc>'' then  pcstresu='ng/mL';
	
	if strip(_speccol)='C49487' then pcstat='NOT DONE';
	pcnam=strip(vvalue(_labid));
 	pcspec=ifc(_SPECPRCF in(' ', '98'), left(upcase(put(_SPECCOLF, $SPECT7F.))), left(upcase(put(_SPECPRCF, $SPECT8F.))));
	pcspccnd=ifc(_SPECCND = '99', upcase(_SPECCNDO), upcase(put(_SPECCND,$SPCCND.)));
	*pcmethod=upcase(put(_TESTMTH,$METHD7F.));
	pclloq=input(_lloq,??best.);
	visitnum=_visit;
	%sdtm_dtc(INVAR_DAT=_SPECDAT, INVAR_TIM=_SPECTIM, OUTVAR_DTC=pcdtc);
	%*sdtm_dtc(INVAR_DAT=_SPECEDAT, INVAR_TIM=_SPECETIM, OUTVAR_DTC=pcendtc);
	pctpt=_PROTSCHD;
	if upcase(pctpt)='PRE- DOSE' then pctptnum=1;
	pctptref=pcgrpid;
	pcrescom=strip(_rescom);
	%sdtm_dtc(INVAR_DAT=_vis_dat, INVAR_TIM=, OUTVAR_DTC=visitdtc);
	module='';
	studyid=_study;
	domain='PC';
	usubjid=catx('/',studyid,_subject);

/*	drop _:;*/
	proc sort;
	by usubjid visitnum pctptnum;

run;

data ex;
	set sdtm.ex;
	keep usubjid exstdtc visitnum;
	proc sort;
	by usubjid visitnum;
run;

data &pgmname.03;
	merge &pgmname.02 (in=a) ex;
	by usubjid visitnum;
	if a;
	PCRFTDTC=exstdtc;
	%sdtm_dy(invar_dtc=&domain.dtc,outvar_dy=&domain.dy);
run;


 
 
/*To derive VISIT */ 
%sdtm_visit(indata = &pgmname.03, outdata=a0&domain.91);

/*To derive EPOCH */ 
%sdtm_epoch(indata = a0&domain.91, outdata=a0&domain.92, domain= &domain., debug=N);

/*To derive Baseline Flag for Findings Domains */ 
%sdtm_blfl(domain = &domain., indata = a0&domain.92, outdata = a0&domain.93 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);
%sdtm_lobxfl(domain = &domain., indata = a0&domain.93, outdata = a0&domain.94 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);

/*To derive --SEQ */ 
%sdtm_seq(indata=a0&domain.94, domain=&domain.);

/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm0;
  set a0&domain.94;
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

