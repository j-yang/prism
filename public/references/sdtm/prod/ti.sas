**************************************************************************;
* Program name      : ti.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ti
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : ti.sas7bdat
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

proc import file="&sdtm_spec" out=ti_spec dbms=xlsx replace;
    range="A1:J500";
    sheet="IETEST";
    getnames=yes;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._spec,outdata=&pgmname.0);
options mprint;
***final dataset****;
data final_sdtm;
  set &pgmname.0;
    DOMAIN='TI';
    STUDYID='D8450C00005';
    IETESTCD=_IETESTCD;
    IETEST=_IETEST;
    IECAT=_IECAT;
    TIVERS=CATS(_TIVERS);
    if not missing(iecat);
run;

%sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 

%trimvarlen(dsin=sdtm.&pgmname.,dsout=sdtm.&pgmname.);;
%logcheck_indi;
