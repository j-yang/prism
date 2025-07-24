**************************************************************************;
* Program name      : ex.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ex
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.EC, RAW.DUMMY_KIT

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_initfmt, %sdtm_init, %logcheck_indi,
					  %sdtm_dtc, %sdtm_dy, %sdtm_visit, %sdtm_epoch, %sdtm_seq, %sdtm_build, %sdtm_suppxx
*
* Output files      : ex.sas7bdat
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
proc format cntlin=raw.cntlin;quit;
%procprint_indi;

/* **************************************************************************; */
/* * Beginning of Programming */
/* **************************************************************************; */

/*Step 1: Apply formats to RAW datasets as needed */
/*Example: %sdtm_initfmt(rawdata=dm vs mh);*/
%sdtm_initfmt(rawdata=ec );


/*Step 2: Shell for SDTM derivation*/
*EC;
%sdtm_init(domain=&pgmname.,rawdata=ec,outdata=ec0i);

data _1z0&domain.0a;
	set ec0i;
	where _ecyn IN ('Yes' 'Y');
	length exacn exslocst exsadper $200.;
	&domain.refid=strip(_kitno);
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
	%sdtm_dtc(invar_dat=_ecstdat, invar_tim=_ecsttim, outvar_dtc=&domain.stdtc);
	%sdtm_dtc(invar_dat=_ecendat, invar_tim=, outvar_dtc=&domain.endtc);

	if _ecacn='Drug permanently discontinued' then exacn='DRUG WITHDRAWN';
	else exacn=strip(upcase(_ecacn));

	exslocst=upcase(coalescec(_ecslosto,_ecslocst));
	exsadper=upcase(coalescec(_ecsadpeo,_ecsadper));

	array cc $200 module  exapreli	exdisc	exadjs	exlpreli ;
	array cco  _module  _ecapreli _ecdisc _ecadjs _eclpreli;

	do i=1 to dim(cc);
		cc(i)=strip(cco(i));
	end;

	array ppu $200 exdosfrm exroute exloc	exlat	exdir	exadj ;
	array ppuo  _ecdosfrm _ecroute  _ecloc _eclat _ecdir _ecadj ;
	do j=1 to dim(ppu);
		ppu(j)=strip(upcase(ppuo(j)));
	end;

	array ppn $200 aespid1	aespid2;
	array ppno _ecaeno1 _ecaeno2;
	do l=1 to dim(ppn);
		if ppno(l)>. then ppn(l)=strip(put(ppno(l),best.));
	end;

run;
proc sort data=_1z0&domain.0a;
	by _subject exrefid;
run;

data dummy_kit;
	set raw.dummy_kit;
run;

%sdtm_init(domain=&pgmname.,rawdata=dummy_kit,outdata=dummy_kit0i);

data _1z0&domain.0a1;
	set dummy_kit0i;
	exrefid=strip(_kitno);
	if find(_KITTYPD,'Eplontersen','i') then extrt='EPLONTERSEN';
	else if find(_KITTYPD,'Placebo','i') then extrt='PLACEBO';
	keep exrefid extrt _subject;
	proc sort;
	by _subject exrefid;
run;


data _z0&domain.0a;
	merge _1z0&domain.0a(in=a drop=extrt) _1z0&domain.0a1;
	by _subject exrefid;
	if a;

	if extrt='EPLONTERSEN' and _ecpdose>. and _ecpdose=0.3 then expstrg=150;
	else if extrt='EPLONTERSEN' and _ecpdose>0 and _ecpdose ne 0.3 then expstrg=56;
	else if extrt='PLACEBO' then expstrg=0;
	if expstrg ne . then expstrgu='mg/mL';

	if nmiss(_ecdstxt,expstrg)=0  then exdose=_ecdstxt*expstrg;
	if exdose>. then exdosu='mg';

run;


/*Step 3: Main body for SDTM derivation*/

%macro sdtm_studyid;
	studyid='D8450C00005';
	usubjid=catx('/',studyid,_subject);
	domain="%upcase(&domain.)";

%mend sdtm_studyid;

data a0&domain.01;
	set _z0&domain.0:;
	%sdtm_studyid;
	%sdtm_dy(invar_dtc=&domain.stdtc,outvar_dy=&domain.stdy);
	%sdtm_dy(invar_dtc=&domain.endtc,outvar_dy=&domain.endy);
	visitnum=_visit;
	proc sort ;
	by usubjid &domain.trt &domain.stdtc;
run;


/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);

/*To derive VISIT */ 
%sdtm_visit(indata = a0&domain.01, outdata=a0&domain.91);

/*To derive EPOCH */ 
%sdtm_epoch(indata = a0&domain.91, outdata=a0&domain.92, domain= &domain., debug=N);

/*To derive Baseline Flag for Findings Domains */ 
*%sdtm_blfl(domain = &domain., indata = a0&domain.92, outdata = a0&domain.93 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);
*%sdtm_lobxfl(domain = &domain., indata = a0&domain.93, outdata = a0&domain.94 , sortby=studyid usubjid &domain.testcd &domain.dtc , groupvar=&domain.testcd, debug = N);

/*To derive --SEQ */ 
%sdtm_seq(indata=a0&domain.92, domain=&domain.);

/*Step 4: Create Main Domain Dataset*/
***final dataset****;
data final_sdtm0;
	set a0&domain.92;
	drop _:;
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

