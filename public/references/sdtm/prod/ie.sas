**************************************************************************;
* Program name      : ie.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ie
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : ie.sas7bdat
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
%sdtm_initfmt(rawdata=ie);


/*Step 2: Shell for SDTM derivation*/
data &pgmname._raw;
	set ie;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw,outdata=&pgmname.0);


/*Step 3: Main body for SDTM derivation*/

data ie1;
	set ie0;
	where _ieyn = 'N';
	iespid = cats(_line,_module_o);
	ietestcd = _ietestcd;
/* 	if not missing(_ietestcd) then number = cats(compress(_ietestcd,'IE','i'),best.); */
	if upcase(_iecat) = 'INCLUSION' then do; ieorres = 'N';end;
	else if upcase(_iecat) = 'EXCLUSION' then do; ieorres = 'Y'; end;
	iecat = upcase(_iecat);
	iestresc = ieorres;
run;

proc sql;
	create table ie1_1 as 
	select a.*, b.DSASPID as dsaspid 
	from ie1 as a left join raw.consent as b on a._subject = b.subject and a._visit = b.visit
;
quit;


proc sql;
	create table ie2 as 
	select a.*, b.IETEST as IETEST_TI 
	from ie1_1 as a left join sdtm.ti as b on a.ietestcd = b.ietestcd and cats(a.dsaspid) = cats(b.tivers)
;
quit;

data ie3;
	set ie2;
	ietest = ietest_ti;
	module = _module;
	STUDYID = 'D8450C00005';
	USUBJID = cats(studyid,'/',_subject);
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=IEDTC);
	%sdtm_dy(invar_dtc=IEDTC,outvar_dy=IEDY);
	visitdtc = _vis_dat;
	domain = 'IE';
	visitnum = _visit;
	if missing(ietest) then ietest = ietestcd;
run;


/*To derive VISIT */ 
%sdtm_visit(indata = IE3, outdata=IE4);

/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain.4, outdata=&domain.5, domain= &domain., debug=N);


/*To derive --SEQ */ 
%sdtm_seq(indata=&domain.5, domain=IE);



/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm;
  set IE5;
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

