**************************************************************************;
* Program name      : ec.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.ec
*
* Author            : You Ye (kpbm747)
*
* Date created      : 2024-01-15
*
* Input datasets    : SDTM.DM, RAW.EC, RAW.OVERDOSE RAW.DUMMY_KIT

* Macros used       : %setup, %localsetup, %procprint_indi, %sdtm_initfmt, %sdtm_init, %logcheck_indi,
                      %sdtm_dtc, %sdtm_dy, %sdtm_visit, %sdtm_epoch, %sdtm_seq, %sdtm_build, %sdtm_suppxx
*
* Output files      : ec.sas7bdat
*
* Usage notes       :  
**************************************************************************;
option mprint;
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
%sdtm_initfmt(rawdata=ec overdose );


/*Step 2: Shell for SDTM derivation*/

*EC;
%sdtm_init(domain=&pgmname.,rawdata=ec,outdata=ec0i);

data _1z0&domain.0a;
    length ecacn ecslocst ecsadper studyper $200.;
    set ec0i;
    &domain.refid=strip(_kitno);
    %sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
    studyper=_studyper;

    array cc $200 module ecdosfrm ecroute ;
    array cco  _module _ecdosfrm _ecroute ;

    do i=1 to dim(cc);
        cc(i)=upcase(cco(i));
    end;
    
    if _ecpdose>. then do;
        ecmood='SCHEDULED';
        %sdtm_dtc(invar_dat=_ecstdat, invar_tim=, outvar_dtc=ecstdtc);
        %sdtm_dtc(invar_dat=_ecendat, invar_tim=, outvar_dtc=ecendtc);
        ecdose=_ecpdose;
        ecdosu=_ecpdoseu;
        output;
    end;
    if _ecyn in ('Yes' 'Y') then do;
        ecmood='PERFORMED';
        %sdtm_dtc(invar_dat=_ecstdat, invar_tim=_ecsttim, outvar_dtc=ecstdtc);
        %sdtm_dtc(invar_dat=_ecendat, invar_tim=, outvar_dtc=ecendtc);
        ecdose=_ecdstxt;
        ecdosu=_ecdosu;
        ecpresp='Y';
        ecoccur=substr(_ecyn,1,1);
        if _ecacn='Drug permanently discontinued' then ecacn='DRUG WITHDRAWN';
        else ecacn=strip(upcase(_ecacn));

        ecslocst=upcase(coalescec(_ecslosto,_ecslocst));
        ecsadper=upcase(coalescec(_ecsadpeo,_ecsadper));


        array ppu $200 ecloc    eclat   ecdir   ecadj    ;
        array ppuo  _ecloc _eclat _ecdir _ecadj  ;
            do j=1 to dim(ppu);
                ppu(j)=strip(upcase(ppuo(j)));
            end;

        array pp $200 ecapreli  ecdisc  ecadjs  eclpreli ;
        array ppo _ecapreli _ecdisc _ecadjs _eclpreli;
            do m=1 to dim(pp);
                pp(m)=strip(ppo(m));
            end;

        array ppn $200 aespid1  aespid2;
        array ppno _ecaeno1 _ecaeno2;
            do l=1 to dim(ppn);
                if ppno(l)>. then  ppn(l)=strip(put(ppno(l),best.));
            end;

        output;
    end;    
run;
proc sort data=_1z0&domain.0a;
    by _subject ecrefid;
run;

*actual dose;

data dummy_kit;
	set raw.dummy_kit;
run;

%sdtm_init(domain=&pgmname.,rawdata=dummy_kit,outdata=dummy_kit0i);

data _1z0&domain.0a1;
    set dummy_kit0i;
    length _ectrt_act $200.;
    ecrefid=strip(_kitno);
    _ectrt_act=strip(upcase(_KITBTHNO));
    keep ecrefid _ectrt_act _subject;
    proc sort ;
    by _subject ecrefid;
run;


data _1z0&domain.0a0sct;
    merge _1z0&domain.0a(in=a) _1z0&domain.0a1;
    by _subject ecrefid;
    if a;
    if  ECMOOD='PERFORMED' then ectrt=_ectrt_act;
run;

*plan dose;
data mer0dm;
    set sdtm.dm;
    _subject=subjid;
    keep _subject armcd;
run;

data _z0&domain.0a;
    merge _1z0&domain.0a0sct(in=a) mer0dm;
    by _subject;
    if a;
    /*
    if ECMOOD='SCHEDULED' and _visit<9 and armcd='E-E' then ectrt='EPLONTERSEN';
    else if ECMOOD='SCHEDULED' and _visit<9 and armcd='P-E' then ectrt='PLACEBO';
    else if ECMOOD='SCHEDULED' and _visit>=9 and armcd>'' then ectrt='EPLONTERSEN';
    */
    ectrt='MASKED';
    if _ecpdose>. and _ecpdose=0.3 then ecpstrg=150;
    else if _ecpdose>0 and _ecpdose^=0.3  then ecpstrg=56;
    if ecpstrg ne . then ecpstrgu='mg/mL';

    *for placebo, -PSTRG will be 0;
    /*
    if ectrt in ('PLACEBO') then ecpstrg=0;
    else if _ecpdose>. and _ecpdose=0.3 then ecpstrg=150;
    else if _ecpdose=0.8 then ecpstrg=56;
    if ecpstrg ne . then ecpstrgu='mg/mL';
    */


run;


*OVERDOSE;
%sdtm_init(domain=&pgmname.,rawdata=overdose,outdata=overdose0i);

data _z0&domain.0b;
    set overdose0i;

    ecmood='PERFORMED';
    ecdose=_odtdos;

    array cc $200 module ecroute  odae  odintent  sodae ectrt  ecdosu  odaetxt1  odaetxt2;
    array cco  _module  _ecroute  _aesod  _odintent _coccoval  _ectrt  _ecdosu  _odaetxt1  _odaetxt2;

    do i=1 to dim(cc);
        cc(i)=cco(i);
    end;

    array ppn $200 aespid1  aespid2   ;
    array ppno _odaeno1 _odaeno2 ;
    do l=1 to dim(ppn);
        ppn(l)=strip(put(ppno(l),best.));
    end;

    %sdtm_dtc(invar_dat=_ecostdat, invar_tim=_ecosttim, outvar_dtc=ecstdtc);
    %sdtm_dtc(invar_dat=_ecoendat, invar_tim=_ecoentim, outvar_dtc=ecendtc);
        
run;

%macro sdtm_studyid;
    studyid='D8450C00005';
    usubjid=catx('/',studyid,_subject);
    domain="%upcase(&domain.)";

%mend sdtm_studyid;
/*Step 3: Main body for SDTM derivation*/
 
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

