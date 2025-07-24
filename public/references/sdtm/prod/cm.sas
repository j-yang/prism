**************************************************************************;
* Program name      : cm.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.cm
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : cm.sas7bdat
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
%*sdtm_initfmt(rawdata=);

proc format;
value $freq
'99'='Other'
'C17998'='Unknown'
'C25473'='QD'
'C64496'='BID'
'C64497'='2 times per week'
'C64498'='QM'
'C64499'='PRN'
'C64510'='QH'
'C64516'='Q2H'
'C64518'='Q4H'
'C64525'='QOD'
'C64526'='1 time per week'
'C64527'='TID'
'C64528'='3 times per week'
'C64529'='Every 4 weeks'
'C64530'='QID'
'C64531'='4 times per week'
'C64535'='Every 3 weeks'
'C64576'='Once'
'C67069'='Every week'
'C71127'='Every 2 weeks'
;
quit;

/*Step 2: Shell for SDTM derivation*/
data sdtm_dm;
  set sdtm.dm;
run;

data &pgmname._raw;
  set raw.cm
  ;
  where cmyn = 'C49488';
run;

data &pgmname._raw1;
    length tmp $2000.;
    set &pgmname._raw;
    tmp=cat(of MEDPREF:);
   
    length cmdecod1-cmdecod10 $200;
    informat cmdecod1-cmdecod10 $200.;
    format cmdecod1-cmdecod10 $200.;
    retain cs 200;
    
    array wraps{10} $200 cmdecod1-cmdecod10;
    if length(tmp)<=cs then 
        do; 
        tsval=trim(left(tmp)); j=1; 
        end;
    else
        do;
        c=1; length=length(tmp); j=1;
        do until(c>length);
            c=c+verify(substr(tmp, c), ' ')-1;
            if c+cs>length then l=length+1-c;
            else
                do;
                l=cs; break=0;
                    do i=(c+cs-1) to c-1 by -1 until(break);
                    if substr(tmp, i+1, 1)=' ' 
/*                         | */
/*                        (substr(tmp, i, 1)='-' & substr(tmp, i+1, 1) ne '-')  */
                       then 
                       do; break=1; l=i+1-c; end;
                    end;
                end;
            wraps{j}=substr(tmp, c, l); 
            c=c+l; j=j+1;
        end;
        end;
    if j>1 then j=j-1;
	if cmdecod1 = '' then cmdecod1 = MEDPREF;
run; 

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw1,outdata=&pgmname.0);

proc format ;
    value  $ny
        "C49487"="N"
        "C49488"="Y"
    ;
quit;
/*Step 3: Main body for SDTM derivation*/
data cm1 ;
  set &pgmname.0;
	STUDYID = _STUDY;
	DOMAIN = 'CM';
	USUBJID= cats(_STUDY, '/', _SUBJECT);
	CMSPID = cats(_CMSPID);
	if cmspid = '.' then call missing(cmspid);
	CMTRT=upcase(strip(_CMTRT));
	CMDECOD = upcase(strip(_MEDPREF));
    CMCAT = 'GENERAL CONCOMITANT MEDICATION';
	*CMPRESP = ifc(_CMOCCUR NE '', 'Y', '');
	*CMOCCUR = put(_CMOCCUR,$NY.);
	CMINDC = upcase(cats(_CMINDC));
	CMCLAS = _ATCDTXT;
	CMCLASCD = _ATCCODE;
	CMDOSE = _CMDOSE;
	CMDOSU = ifc(_CMDOSU='97', 'UNKNOWN', ifc(_CMDOSU='99', 'OTHER', ifc(_CMDOSU='C48542', 'TABLET', ifc(_CMDOSU='C48480', 'CAPSULE', ifc(_CMDOSU='C65060', 'PUFF', put(_CMDOSU, $UNIT6F.))))));
	CMDOSFRM = upcase(putc(_CMDOSFRM,vformat(_CMDOSFRM)));
	CMDOSFRQ = upcase(put(_CMDOSFRQ, $freq.));
	CMDOSTOT = _CMDOSTOT;
	CMROUTE = upcase(putc(_CMROUTE,vformat(_CMROUTE)));
	%SDTM_dtc(INVAR_DAT=_cmstdat ,INVAR_TIM= ,OUTVAR_DTC=CMSTDTC);
	%SDTM_dtc(INVAR_DAT=_cmendat ,INVAR_TIM= ,OUTVAR_DTC=CMENDTC);
 	%sdtm_dy(INVAR_DTC = cmSTDTC , OUTVAR_DY = CMSTDY );
 	%sdtm_dy(INVAR_DTC = CMENDTC , OUTVAR_DY = CMENDY );

/*	CMSTRTPT = ifc(_CMPRIOR EQ 'C49488', 'BEFORE', ' ');*/
/*	CMSTTPT = ifc(_CMPRIOR EQ 'C49488', 'STUDY START', ' ');*/

	CMENRTPT = ifc(_CMONGO= 'C49488', 'ONGOING', ' ');
	CMENTPT = ifc(_CMONGO= 'C49488', 'STUDY TERMINATION', ' ');

	CMDSFRQO = upcase(strip(_CMDOSFO));
	CMREAS = ifc(_CMTREAS='99', upcase(_CMTREASO), upcase(vvalue(_CMTREAS)));
	CMDOSFMO = upcase(strip(_cmdosfro));
	CMDOSUO = strip(_CMDOSUO);
	indcoth = _cmpropo;
	
	
	if _CMMHNO> . then CMMHNO = strip(put(_CMMHNO,best.));
	if _CMMHNO01> . then CMMHNO01 = strip(put(_CMMHNO01,best.));
	if _CMAENO> . then CMAENO = strip(put(_CMAENO,best.));
	if _CMAENO01> . then CMAENO01 = strip(put(_CMAENO01,best.));
	CMCD = _DRUGCODE;

	CMDTXT = _DRUGDTXT;
	CMDTXT2 = _DRGDTXT2;
	CMDTXT3 = _DRGDTXT3;
	CMDTXT4 = _DRGDTXT4;
	CMDTXT5 = _DRGDTXT5;
	CMDTXT6 = _DRGDTXT6;
	CMDTXT7 = _DRGDTXT7;
	CMDTXT8 = _DRGDTXT8;
	atccd = _atccode;
	atcdtxt = _atcdtxt;

	CMDECOD2 = _cmdecod2;
	CMDECOD3 = _cmdecod3;
	CMDECOD4 = _cmdecod4;
	CMDECOD5 = _cmdecod5;
	CMDECOD6 = _cmdecod6;
	CMDECOD7 = _cmdecod7;
	CMDECOD8 = _cmdecod8;

	CMGROUP = _MEDGROUP;
	CMGROUP2 = _MEDGRUP2;
	CMGROUP3 = _MEDGRUP3;
	CMGROUP4 = _MEDGRUP4;
	CMGROUP5 = _MEDGRUP5;
	CMGROUP6 = _MEDGRUP6;
	CMGROUP7 = _MEDGRUP7;
	CMGROUP8 = _MEDGRUP8;

	WHODRGV = _WHODRGV;
	INGRED1 = _MEDGEN1;
	INGRED2 = _MEDGEN2;
	MODULE = ifc(_MODULE ne '',  _MODULE, 'CM');

/*	CMTRTSR = ifc(_CMTRTSR='99' and _CMTRTOTH ne '', upcase({CMTRTOTH), upcase(put((CMTRTSR,$CMTRTSR.)));*/
/*	INDCOTH = _CMPROPO;*/

	CMDECOD2 = upcase(_MEDPREF2);
	CMDECOD3 = upcase(_MEDPREF3);
	CMDECOD4 = upcase(_MEDPREF4);
	CMDECOD5 = upcase(_MEDPREF5);
	CMDECOD6 = upcase(_MEDPREF6);
	CMDECOD7 = upcase(_MEDPREF7);
	CMDECOD8 = upcase(_MEDPREF8);
run;


/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain.1, outdata=&domain., domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain., DOMAIN=&domain.);


/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm;
  set &domain.;
run;

%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/*Step 5: Create Supp-- Dataset*/
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , 
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

