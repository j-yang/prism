**************************************************************************;
* Program name      : mi.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.mi
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.TISBIO

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_initfmt, %sdtm_init, %logcheck_indi,
					  %sdtm_dtc, %sdtm_dy, %sdtm_visit, %sdtm_epoch, %sdtm_seq, %sdtm_build, %sdtm_suppxx,
					  %sdtm_blfl,%sdtm_lobxfl
*
* Output files      : mi.sas7bdat
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
%sdtm_initfmt(rawdata=tisbio);


/*Step 2: Shell for SDTM derivation*/
%sdtm_init(domain=&pgmname.,rawdata=tisbio,outdata=tisbio0i);

%macro test
		(cat=%str('LLTFCAT'),test=%str('Biopsy'),testcd=%str('MIALL'),stat=%str(''),
		res=%str(''),method=%str(''),amyi=%str(''),amyt=%str(''),resoth=%str('')
		);
	&domain.cat=&cat.;
	&domain.test=&test.;
	&domain.testcd=&testcd.;
	&domain.stat=&stat.;
	&domain.orres=&res.;
	&domain.method=&method.;
	amyidoth=&amyi.;
	amytyoth=&amyt.;
	orresoth=&resoth.;
	
	output;
%mend test;

proc format;
	value $spec
		'1', 'Fat' = 'ADIPOSE TISSUE'
		'2', 'Salivary gland' = 'SALIVA'
		'3', 'Rectum' = 'RECTUM'
		'4', 'Bone marrow' = 'BONE MARROW, CORE'
		'5' ,'Myocardium' = 'CARDIAC MUSCLE TISSUE'
		'99', 'Other' = 'OTHER'
;
run;

data _z0&domain.0a;
	length mispid mimethod mispec mispccnd MISPEOTH	amyidoth 	amytyoth  	orresoth   module $200.;
	set tisbio0i;

	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
	%sdtm_dtc(invar_dat=_biopdat, invar_tim=, outvar_dtc=&domain.dtc);
	
	module=strip(_module);
	mispid=strip(_module)||"-"||strip(put(_line,z3.));


	if _biopyn IN ('No' 'N') then do;
		%test(stat='NOT DONE');
		MISPEOTH='';amyidoth='';amytyoth='';orresoth='';mispec='';
	end;
	else if _biopyn IN ('Yes' 'Y') then do;
		mispec=put(_BIOPTIS,$spec.);
		mispccnd='';
		MISPEOTH=_TISOTH;

		if _AMYIRES ne '' then do;
		%test(test=%str('Amyloid Identification'),testcd=%str('AMYID'),res=%str(strip(_AMYIRES)),
			method=%str(catx(";",ifc(_AMMTHOD1 in ('Yes' 'Y'),'Congo Red (+polarized light)',""),
						ifc(_AMMTHOD2 in ('Yes' 'Y'),'Electron Microscopy',""),
						ifc(_AMMTHOD3 in ('Yes' 'Y'),'Other',""))),
			amyi=_AMMEOTH
		);
		end;
		if cmiss(_AMYTRES1,_AMYTRES2,_AMYTRES3) ne 3 then do;
		%test(test=%str('Amyloid Type Identification'),testcd=%str('AMYTYP'),
			res=%str(catx(";",ifc(_AMYTRES1 in ('Yes' 'Y'),'Positive for TTR',""),
						ifc(_AMYTRES2 IN ('Y' 'Yes'),'Positive for AL',""),
						ifc(_AMYTRES3 in ('Yes' 'Y'),'Other',""))),
			method=%str(catx(";",ifc(_ATMTHOD1 in ('Yes' 'Y'),'Mass spectrometry',""),
						ifc(_ATMTHOD2 in ('Yes' 'Y'),'Immunoelectron microscopy',""),
						ifc(_ATMTHOD3 in ('Yes' 'Y'),'Not Performed',""),
						ifc(_ATMTHOD4 in ('Yes' 'Y'),'Other',""))),
			amyt=_AMYTOTH,resoth=_ATRESOTH
		);
		end;
		
	end;
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
	%sdtm_dy(invar_dtc=&domain.dtc,outvar_dy=&domain.dy);
	visitnum=_visit;
	&domain.stresc=&domain.orres;
	proc sort ;
	by usubjid &domain.test &domain.dtc;
run;



/*Please use below macros if applicable */  
%*sdtm_dtc(invar_dat=, invar_tim=, outvar_dtc=);
%*sdtm_dy(invar_dtc=);


/*To derive VISIT */ 
%sdtm_visit(indata = a0&domain.01, outdata=a0&domain.91);

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

