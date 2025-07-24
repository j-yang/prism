**************************************************************************;
* Program name      : ts.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ts
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : ts.sas7bdat
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

proc import file="&sdtm_spec" out=ts_spec dbms=xlsx replace;
    range="A1:m500";
    sheet="TSPARAM";
    getnames=yes;
run;

%sdtm_init(domain=&pgmname.,rawdata=ts_spec,outdata=&pgmname.0);
options mprint;
***final dataset****;
data final_sdtm;
  set &pgmname.0;
  studyid = _studyid;
  domain = _domain;
  tsseq = _tsseq;
  tsgrpid = _tsgrpid;
  tsparmcd = _tsparmcd;
  tsparm = _tsparm;
  tsval = _tsval;
  tsval1 = _tsval1;
  tsval2 = _tsval2;
  tsvalnf = _tsvalnf;
  tsvalcd = _tsvalcd;
  tsvcdref = _tsvcdref;
  tsvcdver = _tsvcdver;
run;

%sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 

%trimvarlen(dsin=sdtm.&pgmname.,dsout=sdtm.&pgmname.);;
%logcheck_indi;
