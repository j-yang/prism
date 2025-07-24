**************************************************************************;
* Program name      : ta.sas
*
* Program path      : root/cdar/d845/d8450c00005/ar/pre_dr1/sdtm/dev/program/
*
* Type              : SAS program
*
* Purpose           : Creation of sdtm.ta
*
* Author            : Jimmy Yang
*
* Date created      : 2024-01-15
*
* Input datasets    : TA_INFO Tab
*
* Macros used       : 
*
* Output files      : sdtm.ta
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

**************************************************************************;
* Setup calls
**************************************************************************;
/* %setup; */
/* %localsetup; */

proc import file="&sdtm_spec" out=ta_spec dbms=xlsx replace;
    range="A1:h9";
    sheet="TA_INFO";
    getnames=yes;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._spec,outdata=&pgmname.0);

***final dataset****;
data final_sdtm;
  set &pgmname.0;
    ARM=_ARM;
    ARMCD=_ARMCD;
    DOMAIN='TA';
    ELEMENT=_ELEMENT;
    EPOCH=_EPOCH;
    ETCD=_ETCD;
    STUDYID='D8450C00005';
    TABRANCH=_TABRANCH;
    TAETORD=_TAETORD;
    TATRANS=_TATRANS;
run;

%sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 

/*Assign minimal lengths to varibales */

  %trimvarlen(dsin=sdtm.&pgmname.,dsout=sdtm.&pgmname.);; 


%logcheck_indi;
