**************************************************************************;
* Program name      : tv_kjcj731.sas
*
* Program path      : root/cdar/d845/d8450c00005/ar/pre_dr1/sdtm/dev/program/
*
* Type              : SAS program
*
* Purpose           : Creation of sdtm.tv
*
* Author            : Jimmy Yang
*
* Date created      : 2024-01-15
*
* Input datasets    : TVVISIT Tab
*
* Macros used       : 
*
* Output files      : sdtm.tv
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


proc import file="&sdtm_spec" out=tv_spec dbms=xlsx replace;
    range="A1:E34";
    sheet="TVVISIT";
    getnames=yes;
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._spec,outdata=&pgmname.0);
options mprint;
***final dataset****;
data final_sdtm;
  set &pgmname.0;

    ARMCD='';
    DOMAIN='TV';
    STUDYID='D8450C00005';
    TVENRL=_TVENRL;
    TVSTRL=_TVSTRL;
    VISIT=_VISIT;
    VISITDY=_VISITDY;
    VISITNUM=_VISITNUM;
run;

%sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 

%trimvarlen(dsin=sdtm.&pgmname.,dsout=sdtm.&pgmname.);;
%logcheck_indi;

