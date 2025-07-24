**************************************************************************;
* Program name      : te.sas
*
* Program path      : root/cdar/d845/d8450c00005/ar/PRE_dr1/sdtm/dev/program/
*
* Type              : SAS program
*
* Purpose           : Creation of sdtm.te
*
* Author            : Jimmy Yang
*
* Date created      : 2021-12-27
*
* Input datasets    : TE_INFO Tab
*
* Macros used       : 
*
* Output files      : sdtm.te
*
* Usage notes       :  
**************************************************************************;
%setup(version=260,
	   localsetup=root/cdar/%scan(&_exec_programpath.,3,/)/%scan(&_exec_programpath.,4,/)/ar/%scan(&_exec_programpath.,6,/)/common/%scan(&_exec_programpath.,8,/)/macro/localsetup.sas);

%localsetup;

proc datasets lib=work kill nowarn nodetails nolist mt=data;
quit;

%let PGMNAME=%scan(&_EXEC_PROGRAMNAME,1, ".");
%procprint_indi;

proc import file="&sdtm_spec" out=te_spec dbms=xlsx replace;
    range="A1:e6";
    sheet="TE_INFO";
    getnames=yes;
run;


%sdtm_init(domain=&pgmname.,rawdata=&pgmname._spec,outdata=&pgmname.0);

***final dataset****;
data final_sdtm;
  set &pgmname.0;
  DOMAIN='TE';
    ELEMENT=_ELEMENT;
    ETCD=_ETCD;
    STUDYID='D8450C00005';
    TEDUR=_TEDUR;
    TEENRL=_TEENRL;
    TESTRL=_TESTRL;
run;

%sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 


/*Assign minimal lengths to varibales */
%trimvarlen(dsin=sdtm.&pgmname.,dsout=sdtm.&pgmname.);; 

%logcheck_indi;
