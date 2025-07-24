**************************************************************************;
* Program name      : ce.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ce
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.LIVERSS, RAW.STOPR, RAW.DEATHEVT, RAW.RPCE

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_initfmt, %sdtm_init, %logcheck_indi,
					  %sdtm_dtc, %sdtm_dy, %sdtm_visit, %sdtm_epoch, %sdtm_seq, %sdtm_build, %sdtm_suppxx
*
* Output files      : ce.sas7bdat
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
%sdtm_initfmt(rawdata=liverss stopr deathevt rpce);


/*Step 2: Shell for SDTM derivation*/

%sdtm_init(domain=&pgmname.,rawdata=liverss,outdata=liverss0i);


**LIVERSS;
data _z0&domain.0a;
	length cespid ceterm cepresp ceoccur cepatt cespfy $200.;
	set liverss0i;
	cespid=strip(put(_cecspid,best.));
	ceterm=ifc(_cecterm in('Rash','Lymphadenopathy', 'Other 1', 'Other 2'), trim(left(_cecterm))||':'||trim(left(_cetermo)), _cecterm);
	cepresp='Y';
	ceoccur=substr(_ceoccur,1,1);
	if _cecpatt='C49488' then cepatt='INTERMITTENT';
	%sdtm_dtc(invar_dat=_cestdat, invar_tim=, outvar_dtc=cestdtc);
	%sdtm_dtc(invar_dat=_ceendat, invar_tim=, outvar_dtc=ceendtc);
	cespfy=_livsstxt;
	*%sdtm_dtc(invar_dat=vis_dat, invar_tim=, outvar_dtc=visitdtc);

	array cc $200 cecat cellt cedecod cehlt cehlgt cebodsys cesoc meddrav module;
	array cco  _cecat _llt_name _pt_name _hlt_name _hlgt_name _soc_name _soc_name _meddra_v _module;

	array nn 8. celltcd ceptcd cehltcd cehlgtcd cebdsycd cesoccd;
	array nno _llt_code _pt_code _hlt_code _hlgt_code _soc_code _soc_code;

	do i=1 to dim(cc);
		cc(i)=strip(cco(i));
	end;
	do j=1 to dim(nn);
		nn(j)=nno(j);
	end;
run;

**STOPR;
%sdtm_init(domain=&pgmname.,rawdata=stopr,outdata=stopr0i);

data _z0&domain.0b;
	length cespid ceterm cepresp ceoccur $200.;
	set stopr0i;
	cespid=strip(_module)||'-'||strip(put(_line,z3.));
	ceterm=vvalue(_stoprce);
	cepresp='Y';
	ceoccur='Y';

	%sdtm_dtc(invar_dat=_stopdat, invar_tim=, outvar_dtc=cestdtc);
	%sdtm_dtc(invar_dat=_resdat, invar_tim=, outvar_dtc=ceendtc);
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);

	array cc $200 cecat stmetwk strslvwk module;
	array cco  _stoprcat _stovisit _resvisit  _module;


	do i=1 to dim(cc);
		cc(i)=strip(cco(i));
	end;
run;

**DEATHEVT;
%sdtm_init(domain=&pgmname.,rawdata=deathevt,outdata=deathevt0i);
data _z0&domain.0c;
	length cecat cespid ceterm cepresp ceoccur module $200.;
	set deathevt0i;
	cespid=strip(_module)||'-'||strip(put(_aeno,best.));
	ceterm=vvalue(_ceterm);
	cepresp='Y';
	ceoccur='Y';
	cecat='DEATH EVENT';
	module=_module;

	%sdtm_dtc(invar_dat=_aesddat, invar_tim=, outvar_dtc=cestdtc);
run;

**RPCE;
%sdtm_init(domain=&pgmname.,rawdata=rpce,outdata=rpce0i);

data _z0&domain.0d;
	length cecat cespid ceterm cepresp ceoccur module $200.;
	set rpce0i;
	where _RPCEYN in ('Yes' 'Y');
	cespid=strip(_module)||'-'||strip(put(_line,z3.));
	ceterm=vvalue(_rpcetyp);
	cepresp='Y';
	ceoccur='Y';
	cecat='CV Death or Recurrent Predefined Clinical Events';
	module=_module;

	ceaeyn=substr(_rpceaeyn,1,1);
	if _rpaenum>. then ceaenum=strip(put(_rpaenum,best.));
	ceongo=substr(_ceongo,1,1);


	%sdtm_dtc(invar_dat=_cestdat, invar_tim=, outvar_dtc=cestdtc);
	%sdtm_dtc(invar_dat=_ceendat, invar_tim=, outvar_dtc=ceendtc);
	%sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
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

	ceterm=upcase(ceterm);

	proc sort ;
	by usubjid cecat ceterm cestdtc;
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

