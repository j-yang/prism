**************************************************************************;
* Program name      : cv.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.cv
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2025-07-09
*
* Input datasets    : SDTM.DM, RAW.ECHOC1

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : cv.sas7bdat
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
options validvarname=upcase;
proc format cntlin=raw.cntlin; run;
%procprint_indi;

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
%*sdtm_initfmt(rawdata=ECHOC1);


/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
	set raw.ECHOC1;
run;


***For SEQ, &&&domain.sort_order;
%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/

proc import datafile="&sdtm_spec" out=cvtest dbms=xlsx replace;
sheet="CVTEST";
run;



data cvtest1;
	set cvtest;
	length a_whr a_cat a_dtc a_testcd a_test a_res a_unit a_unit1 a_sires a_sin a_supp1 a_supp2 $200.;
	where CONVERSION_DEFINITION>'';
	a_whr=CONVERSION_DEFINITION;
	a_cat= strip(compress(tranwrd(CVCAT,'Set to',''),'.'));
	a_dtc='cvdat';
	a_testcd=cvtestcd;
	a_test=cvtest;

	_a_res= strip(compress(tranwrd(tranwrd(CVORRES,'Set to character form of',''),'Set to','')));
	if substr(_a_res, length(strip(_a_res)), 1) = '.' then
        _a_res = substr(_a_res, 1, length(strip(_a_res)) - 1);
	if find(CVORRES,'Set to character form of','i') then a_res="strip(put("||strip(_a_res)||",best.))";
	else a_res=_a_res;

	
	if find(CVORRESU,'Set to','i')>0 then a_unit1=strip(compress(tranwrd(CVORRESU,'Set to','')));
	else a_unit1="''";
	if find(CVORRESU,'Set to','i')=0 then a_unit=CVORRESU;

	_a_sires= strip(compress(tranwrd(tranwrd(CVSTRESC,'Set to character form of',''),'Set to','')));
	if substr(_a_sires, length(strip(_a_sires)), 1) = '.' then
        _a_sires = substr(_a_sires, 1, length(strip(_a_sires)) - 1);
	if find(CVSTRESC,'Set to character form of','i') then a_sires="strip(put("||strip(_a_sires)||",best.))";
	else a_sires=_a_sires;

	a_sin=CVSTRESN;
	if a_sin='' then a_sin='.';
	a_supp1=COM_IN_SUPP;
	a_supp2=OTHER_INFO_IN_SUPP;
	a_len1=length(a_testcd);
	a_len2=length(a_test);
	if a_len1>8 then put 'STAR_C' 'HECK: The length of CVTESTCD exceeds 8, CVTESTCD=' a_testcd;
	if a_len2>40 then put 'STAR_C' 'HECK: The length of CVTESTCD exceeds 40, CVTESTCD=' a_test;
	a_ord=_n_;
	keep a_:;

run;

data cvtest2;
	set cvtest1;
run;

%let suppkeep=%str(ECIMAGEQ		ECIMQRE1	ECIMQRE2	ECIMQRE3	ECIMQRE4	ECIMQRE5 ECIMQOCO);
data vlm_execute;
	set cvtest2;
	length runcode $2000;
	runcode="data _z_"||strip(a_testcd)||"_"||strip(put(a_ord,best.))||"; "||
			" set &pgmname._raw; "||
			"length cvcat cvtest cvtestcd cvorres cvorresu cvstresc  $200.;"||
			strip(a_whr)||" then do; "||
				"cvcat="||strip(a_cat)||"; cvtest="||'"'||strip(a_test)||'"'||"; cvtestcd='"||strip(a_testcd)||"';"||
				"cvorres="||strip(a_res)||"; if cvorres ne '' then cvorresu='"||strip(a_unit)||"';"||
				"if cvorres ne '' and cvorresu='' then cvorresu="||strip(a_unit1)||";"||
				"cvstresc="||strip(a_sires)||"; cvstresn="||strip(a_sin)||";"||
				"visitnum=visit;CVMETHOD=upcase(put(CVMETHOD,$METHD8F.));"||
				"output; end; "||
				"keep subject visitnum cv: vis_dat "||strip(a_supp1)||" "||strip(a_supp2)||" &suppkeep ;"
			;
 	call execute(runcode); 
run;


data a0&domain.01;
	set _z_:;
	proc sort;
	by subject cvdat cvtestcd;
run;



%macro sdtm_studyid;
	studyid='D8450C00005';
	usubjid=catx('/',studyid,subject);
	domain="%upcase(&domain.)";

%mend sdtm_studyid;


data a0&domain.02;
	set a0&domain.01;
	%sdtm_studyid;
	%sdtm_dtc(invar_dat=vis_dat, invar_tim=, outvar_dtc=visitdtc);
	%sdtm_dtc(invar_dat=cvdat, invar_tim=, outvar_dtc=&domain.dtc);
	if cvstresc ne '' and cvorresu ne '' then cvstresu=cvorresu;

	array ny ECIMAGEQ	ECPEREFS	ECIMQRE1	ECIMQRE2	ECIMQRE3	ECIMQRE4	ECIMQRE5;
	do i=1 to dim(ny);
		ny(i)=upcase(put(ny(i),$NY.));
	end;
	ECIMQOCO=upcase(ECIMQOCO);


run;


data a0&domain.03;
	set a0&domain.02;
	%sdtm_dy(invar_dtc=&domain.dtc,outvar_dy=&domain.dy);
	epoch='';
run;

/*Please use below macros if applicable */  
/*To derive VISIT */ 
%sdtm_visit(indata = a0&domain.03, outdata=a0&domain.91);

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

