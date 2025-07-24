**************************************************************************;
* Program name      : sv.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.sv
*
* Author            : Jimmy Yang (ktxv525)
*
* Date created      : 2024-01-15
*
* Input datasets    : 

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : sv.sas7bdat
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
%*sdtm_initfmt(rawdata=visit);

/*Step 2: Shell for SDTM derivation*/
options mprint;
proc format;
	value $vecntmod
	"1"="Remote-audio"
"2"="Remote-video" 
"3"="On-site visit"
"4"="Home visit"
"99"="Other"
;
quit;

proc sql noprint;
	create table sv0 as 
	select distinct SUBJECT, subject as subjid, module, visit as visitnum,visit as _visit,
						max(input(vis_dat,yymmdd10.)) as svendt format yymmdd10.,
	min(input(vis_dat,yymmdd10.)) as svstdt format yymmdd10.,
	ifc(visitnd ne '','Y','') as VISITND,
	ifc(vecntmod='99',upcase(vecnmodo),upcase(put(vecntmod,$vecntmod.))) as svcntmod,
/* 	ifc(vespchgi = 'Y','Y','') as svspchg,  */
	MODULE_O, VECNTMOD, VECNMODO,VESPCHGI
	from raw.visit
	group by subject,visit
	;
quit;

**multiple visit model collected in the same visit;
data visit_1;
  length VECNTMOD_c $100.;
  set sv0;
  if  module_o ne . then module_o_c = strip(put(module_o,best.));
  if VECNTMOD ne '' then VECNTMOD_c = propcase(strip(put(VECNTMOD,$cntmd3f.)),'*');
  *if VECNTMOD eq '99' then VECNTMOD_c = strip(VECNMODO);
  if VECNTMOD ne '' then VECNTMOD_n = input(VECNTMOD,best.);
  if VESPCHGI ne '' then VESPCHGI_c = vvalue(VESPCHGI);
  VECNMDO = VECNMODO;
run;

proc sort data=	visit_1;
  by subject _visit module module_o VECNTMOD;
run;

data visit_1;
  set visit_1;
  by subject _visit module module_o VECNTMOD;
  if first._visit then ord = 1;
  else ord+1;

proc transpose data= visit_1 prefix=MODULEO out=visit_m;
  where module_o_c ne '';
  by subject _visit;
  var module_o_c;
  id ord;
run;

proc transpose data= visit_1 prefix=VECNMOD out=visit_v;
  where   VECNTMOD ne '';
  by subject _visit;
  var VECNTMOD_c;
  id ord;
run;

proc transpose data= visit_1 prefix=SVSPCHG out=visit_sh;
  where   VESPCHGI ne '';
  by subject _visit;
  var VESPCHGI_c;
  id ord;
run;

proc transpose data= visit_1 prefix=n_VECNTMOD out=visit_vn;
  where   VECNTMOD_n ne .;
  by subject _visit;
  var VECNTMOD_n;
  id ord;
run;

proc transpose data= visit_1 prefix=VECNMDO out=visit_do;
  where   VECNMDO ne '';
  by subject _visit;
  var VECNMDO;
  id ord;
run;

proc sort data= sv0;
  by subject _visit;
run;

proc sort data=	visit_1 out=visit_s nodupkey;
  by subject _visit VESPCHGI;
  where VESPCHGI ne '';
run;

data sv11;
  length VECNTMOD: $100.;
  merge sv0(in=a)
  visit_m(in=b keep=subject _visit module:)
  visit_v(in=c keep=subject _visit VECNMOD:)
  visit_vn(in=cn keep=subject _visit n_VECNTMOD:)
  /*visit_s(in=d keep=subject _visit VESPCHGI)*/
  visit_sh(in=e keep = subject _visit SVSPCHG:)
  visit_do(in=f keep = subject _visit VECNMDO:);
  by subject _visit;
  if a;
  cc=n(of n_VECNTMOD:);
  if cc >1 then SVCNTMOD = 'MULTIPLE';
  if cc >2 then put "STAR_CH" "ECK: current spec define three more VISIT module is not enough, please check and update spec:"
  subject = " and " visitnum = ;
  drop _visit ;
run; 

/*Step 3: Main body for SDTM derivation*/

%sdtm_init(domain=&pgmname.,rawdata=sv11,outdata=sv1);

    proc sql;
        create table sv2 as 
			select a.*, tv.visit as _tv_visit length=40
					
            from sv1 as a left join 
		(select distinct 
            visitnum, visit from sdtm.tv) as tv on cats(int(a._visitnum))=cats(tv.visitnum)
           ;
    quit;

    data sv3;
        set sv2;
        length _VISIT $40;
		visitnum = _visitnum;
        if visitnum ne . and ( visitnum=int(visitnum) or visitnum = 1.1) then
            do;
                _visit=_tv_visit;
             
                if missing(_visit) then
                    put "STAR_C" "HECK: Missing visit name for visit number " visitnum=;
            end;
        else if visitnum ne .  and visitnum ^=int(visitnum) and visitnum ne 1.1 then
            do;
   
                    _visit=strip(_tv_visit)||cat("_Unscheduled Visit_", visitnum);
            
            end;
         drop _tv_visit ;
    run;


data sv;
	set sv3;
	studyid = "D8450C00005";
	domain = "&domain.";
	usubjid=cats(studyid,  '/',   _subjid); 
	subjid = _subjid;
	visit = _visit;
	svstdtc = put(_svstdt,yymmdd10.);
	svendtc = put(_svendt,yymmdd10.);
     if cats(svstdtc) = '.'  then call missing(svstdtc);
     if cats(svendtc) = '.'  then call missing(svendtc);
	if not missing(put(usubjid,rfstdtc.)) and not missing(svstdtc) then do;
	%sdtm_dy(INVAR_DTC = &pgmname.stdtc , OUTVAR_DY = &pgmname.stdy );
	%sdtm_dy(INVAR_DTC = &pgmname.endtc , OUTVAR_DY = &pgmname.endy );
	end;
     if visitnum = 1.1 then visit = 'RE-SCREENING';
     svcntmod = _svcntmod;
     moduleo1 = _moduleo1;
     moduleo2 = _moduleo2;
	VECNMOD1 = _VECNMOD1;
	VECNMOD2 = _VECNMOD2;
	svspchg1 = _svspchg1;
	vecnmdo1 = _vecnmdo1;
	*vecnmdo2 = _vecnmdo2;
	visitnd = _visitnd;
proc sort nodupkey; by usubjid visitnum;
run;



/*To derive EPOCH */ 
%sdtm_epoch(indata=&domain., outdata=&domain., domain= &domain., debug=N);

/*To derive --SEQ */ 
%sdtm_seq(indata=&domain., domain=&domain.);


/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm;
  set _last_;
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

