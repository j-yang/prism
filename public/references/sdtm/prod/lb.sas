**************************************************************************;
* Program name      : lb.sas
*
* Program path      : root/cdar/d845/D8450C00005/ar/pre_dr1/sdtm/dev/program
*
* Type              : SAS program
*
* Purpose           : To create sdtm.lb
*
* Author            : Zifan Guo (knfg575)
*
* Date created      : 2024-06-04/2024-07-19
*
* Input datasets    : RAW.LB, RAW.CLAB, RAW.PREG, RAW.BMRES

* Macros used       : %setup, %localsetup, %procprint_indi
*
* Output files      : lb.sas7bdat
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
/*%sdtm_initfmt(rawdata=);*/


/*Step 2: Shell for SDTM derivation*/
data raw_lb;
    length lbcat $40.;
    set raw.lb;
    lbcat = upcase(putc(lbcat, vformat(lbcat)));
    lbspid = 'L'||strip(lbtest);
run;

* add BMRES dataset to LB;

data lb_bmres (drop=visittyp);
    length lbcat $40. lborres $200. lborresu $200. _visitmod $200.;
    set raw.dummy_bmres (in=ada drop=patient) raw.dummy_bmres1 (in=bm drop=patient) raw.dummy_bmres2 (in=pd drop=patient);
    lbrefid = specid;
    lbspid = "L"||strip(BMCODE);
/*     lbtestcd = "L"||strip(BMCODE); */
    lbtest = put(bmcode, $labcode.);
    if ada then lbcat = "ANTIDRUG ANTIBODIES";
    else if bm then lbcat = "BIOCHEMICAL BIOMARKER";
    else if pd then lbcat = "TTR CONCENTRATION";
    lbmethod = upcase(lbmethod);
    lblloq = input(lbclloq, best.);
    lbuloq = input(lbculoq, best.);
    lbtpt = protschd;
    lbtype = upcase(put(labtype, $lbtyp1f.));
/*     module = ifc() */
    sampcom = bmcom;
    _visitmod = upcase(put(VISITMOD,$VISMOD.));
    
    
run;

data &pgmname._raw;
length lbspid $25. lbtest $40. lbcat $40. lborres $200. lborresu $200. _visitmod $200. SPCANDTC $200.;
    set raw.clab (in=a where=(lbctstcd not in ('02H80' '02K11'))) raw_lb (in=b) raw.preg (in=c where=(asm_app='C49488')) lb_bmres;
    format _all_;
    if a then do;
        lbspid = 'L'||strip(lbctstcd);
        module = "CLAB";
        _visitmod = upcase(put(VISITMOD,$VISMOD.));
        _visittyp = upcase(ifc(visittyp="1","Scheduled",ifc(visittyp="2","Unscheduled","")));
        lbnam = ifc(lbnam ne '', upcase(lbnam), ifc(lbnam='', putc(lbnum, vformat(lbnum)), ''));
        if lbtstdat ne '' then spcandtc = strip(lbtstdat)||"T"||strip(lbtsttim);
    end;

run;

data uniconv;
    set raw.raw_uniconv;
    lbspid = 'L'||strip(uctestcd);
run;

proc sort data=uniconv (keep=lbspid lborresu lbstresu factnom) 
            out=uniconv0 nodupkey; 
by lbspid lborresu lbstresu factnom; run;
data uniconv0;
    set uniconv0;
    ucorresu = lborresu;
run;
proc sort data=uniconv (keep=lbspid ucorresu lborresu lbstresu factnom ) 
            out=uniconv1 nodupkey; 
by lbspid ucorresu lborresu lbstresu factnom; run;
data uniconv;
    set uniconv0 uniconv1;
    proc sort nodupkey;
    by lbspid ucorresu lborresu lbstresu factnom;
run;

proc sort data=raw.raw_lbref (keep=aztestcd azcat lbtestcd lbtest lbspec lbstresu) 
            out=lbref nodupkey; 
by aztestcd azcat lbtestcd lbtest lbspec lbstresu; run;

proc sql;
    create table lb_raw0 as
    select distinct a.*, b.lborresu, b.lbstresu, b.factnom 
    from lb_raw (rename=(lborresu=ucorresu)) as a
    left join uniconv0 as b
    on a.lbspid = b.lbspid and a.ucorresu=b.ucorresu;
    create table lb_raw1 as
    select distinct a.*, b.lborresu as lborresu1, b.lbstresu, b.factnom 
    from lb_raw0 (where=(missing(lborresu)) drop=lbstresu factnom) as a
    left join uniconv1 as b
    on a.lbspid = b.lbspid and a.ucorresu=b.ucorresu;
quit;
data lb_raw2;
    set lb_raw0 (where=(^missing(lborresu))) lb_raw1;
    if missing(lborresu) then lborresu = lborresu1;
run;
proc sql;
    create table lb_raw3 as
    select a.*, b.azcat, b.lbtestcd, b.lbtest, b.lbspec as azspec from lb_raw2 (drop=lbtest) as a 
    left join lbref as b 
    on a.lbspid=b.aztestcd /*and a.lbstresu=b.lbstresu*/;
quit;

data lb_raw4;
    set lb_raw3;
    if module = "PREG" then do;
        lbspec = "URINE";
        if ASM_APP = 'C49488' then do;
            lbtestcd = 'HCG';
            lbcat = 'PREGNANCY TEST';
            lbtest = 'Choriogonadotropin Beta';
            lbdat = samp_dat;
        end;
        if ASM_APP = 'C49488' and pregtstu = '1' then lborres = 'POSITIVE';
        else if ASM_APP = 'C49488' and pregtstu = '0' then lborres = 'NEGATIVE';
    end;
    if module = "CLAB" then do;
        LBREASND = ifc(lbstat eq 'NOT DONE', lbcoval2, '');
        LBRESCOM = ifc(lbstat ne 'NOT DONE', lbcoval2, '');
        SAMPCOM = lbcoval1;
        _LBFAST = put(LBFAST, $NYU.);
    end;
    if /*^missing(azcat) and */module="CLAB" or index(module,"LB") then lbcat = azcat;
    if ^missing(azspec) and (index(module,"LB") or module="CLAB") then lbspec=azspec;
    if LBPERF = 'C49487' or LBSTAT = 'NOT DONE' then do;
        lbtest = "Lab Data";
        lbtestcd = "LBALL";
        LBSTAT = 'NOT DONE';
    end;
run;


data lb_raw5;
    set lb_raw4;
    length LBNRIND $20. signal $2.;
    if module = "PREG" then lbstresc = lborres;
    else if /*(index(module,"LB")>0 or module = "CLAB") and */(strip(compress(lborres,"1234567890")) ^= strip(lborres)) and (factnom ^= 1 and ^missing(factnom)) then do;
        resn = input(compress(lborres,"<>="),?? best.);
        if index(lborres, "<") > 0 then signal="<";
        else if index(lborres, ">") > 0 then signal=">";
        if index(lborres, "<=") > 0 then signal="<=";
        else if index(lborres, ">=") > 0 then signal=">=";
        lbstresc = strip(strip(signal)||strip(put(resn*factnom,best.)));
        lbstresn = ifn(missing(signal) and ^missing(lbstresc), input(lbstresc,?? best.), .);
    end;
    else if factnom=1 or missing(factnom) then do;
/*  Remove the useless zero in lbstresc from lborres, like '3.00', '<3.0' */
        if index(lborres, "<") > 0 then signal="<";
        else if index(lborres, ">") > 0 then signal=">";
        if index(lborres, "<=") > 0 then signal="<=";
        else if index(lborres, ">=") > 0 then signal=">=";
        if index(lborres, "<") > 0 or index(lborres, ">") > 0 then do;
            resn = input(compress(lborres,"<>="),?? best.);
            lbstresc = strip(strip(signal)||strip(put(resn*1,best.)));
        end;
        else lbstresc = ifc(strip(compress(lborres,"1234567890.")) = "", strip(put(input(lborres,?? best.),best.)), lborres);
        lbstresn = ifn(^missing(lbstresc) and strip(compress(lborres,"1234567890.")) = "", input(lbstresc,?? best.), .);
        lbstnrlo = ifn(^missing(lbstresc), input(lbornrlo, ??best.), .);
        lbstnrhi = ifn(^missing(lbstresc), input(lbornrhi, ??best.), .);
    end;
    if ^missing(lbornrlo) and ^missing(factnom) then do;
        if index(lbornrlo,"<") > 0  then do;
            lon = input(compress(lbornrlo, "<"), ?? best.);
            deci_lo = length(scan(lbornrlo, 2, "."))+1;
            lbstnrlo = round(lon*factnom, 1/10**(deci_lo-1));
        end;
        else if index(lbornrlo,">") > 0  then do;
            lon = input(compress(lbornrlo, ">"), ?? best.);
            deci_lo = length(scan(lbornrlo, 2, "."))+1;
            lbstnrlo = round(lon*factnom, 1/10**(deci_lo+1));
        end;
        else if strip(compress(lbornrlo,"0123456789."))="" then do;
            lon = input(lbornrlo, ?? best.);
            deci_lo = length(scan(lbornrlo, 2, "."))+1;
            lbstnrlo = lon*factnom;
        end;
    end;
    if ^missing(lbornrhi) and ^missing(factnom) then do;
        if index(lbornrhi,"<") > 0  then do;
            hin = input(compress(lbornrhi, "<"), ?? best.);
            deci_hi = length(scan(lbornrhi, 2, "."))+1;
            lbstnrhi = round(hin*factnom, 1/10**(deci_hi-1));
        end;
        else if index(lbornrhi,">") > 0  then do;
            hin = input(compress(lbornrhi, ">"), ?? best.);
            deci_hi = length(scan(lbornrhi, 2, "."))+1;
            lbstnrhi = round(hin*factnom, 1/10**(deci_hi+1));
        end;
        else if strip(compress(lbornrhi,"0123456789."))="" then do;
            hin = input(lbornrhi, ?? best.);
            deci_hi = length(scan(lbornrhi, 2, "."))+1;
            lbstnrhi = hin*factnom;
        end;
    end;
    if ^missing(lbstnrlo) and ^missing(lbstnrhi) then do;
        if lbstnrlo <= lbstresn <= lbstnrhi then lbnrind = "NORMAL";
        else if .<lbstresn < lbstnrlo then lbnrind = "LOW";
        else if lbstresn > lbstnrhi then lbnrind = "HIGH";
    end;
    else if ^missing(lbstnrlo) and missing(lbstnrhi) then do;
        if .<lbstresn < lbstnrlo then lbnrind = "LOW";
        else if lbstresn >= lbstnrlo then lbnrind = "NORMAL";
    end;
    else if ^missing(lbstnrhi) and missing(lbstnrlo) then do;
        if .<lbstresn <= lbstnrhi then lbnrind = "NORMAL";
        else if lbstresn > lbstnrhi then lbnrind = "HIGH";
    end;
    else if missing(lbstnrhi) and missing(lbstnrlo) then call missing(lbnrind);
    if index(lbstresc, ">")>0 and input(compress(lbstresc, ">"),??best.) >= lbstnrhi >. then lbnrind="HIGH";
    else if index(lbstresc, "<")>0 and .<input(compress(lbstresc, "<"),??best.) <= lbstnrlo then lbnrind="LOW";
    else if index(lbstresc, "<")>0 and lbstnrlo=0 then lbnrind="NORMAL";
    if cmiss(factnom,lborres)=0 and cmiss(LBSTRESN,LBSTRESC)=2 then LBSTRESC=LBORRES;
    if missing(lbstresc) then call missing(lbstresu);
run;

%sdtm_init(domain=&pgmname.,rawdata=&pgmname._raw5,outdata=&pgmname.0);

/* Step 3: Main body for SDTM derivation */
data lb1;
    set lb0;
    studyid = "D8450C00005";
    domain = 'LB';
    usubjid = catx("/",STUDYID,_SUBJECT);
    LBSPID = _LBSPID;
    LBREFID = _LBREFID;
    LBTESTCD = _LBTESTCD;
    LBTEST = _LBTEST;
    LBCAT  = _LBCAT ;
    LBORRES  = ifc(_LBORRES in ("" "."),"",_LBORRES) ;
    LBORRESU  = _LBORRESU ;
    if missing(lborres) then lborresu = '';
    LBORNRLO  = _LBORNRLO ;
    LBORNRHI  = _LBORNRHI ;
    LBSTRESC  = ifc(_LBSTRESC in ("" "."),"",_LBSTRESC) ;
    LBSTRESN  = _LBSTRESN ;
    LBSTRESU  = _LBSTRESU ;
    if missing(lborresu) then LBSTRESU = '';
    LBSTNRLO  = _LBSTNRLO ;
    LBSTNRHI  = _LBSTNRHI ;
    LBNRIND  = _LBNRIND ;
    LBSTAT  = _LBSTAT ;
    LBREASND = _LBREASND;
    LBLOINC = _LBLOINC;
    LBSPEC  = _LBSPEC ;
    LBFAST = __LBFAST;
    VISITNUM = _VISIT;
    VISITMOD = __VISITMOD;
    VISITTYP = __VISITTYP;
    LBRESCOM = _LBRESCOM;
    SAMPCOM = _SAMPCOM;
    LBTPT = _LBTPT;
    LBNAM = _LBNAM;
    LBSPCCND = _LBSPCCND;
    %sdtm_dtc(invar_dat=_lbdat, invar_tim=_lbtim, outvar_dtc=lbdtc);
    %sdtm_dy(invar_dtc=lbdtc, outvar_dy=lbdy);
    %sdtm_dtc(invar_dat=_vis_dat, invar_tim=, outvar_dtc=visitdtc);
    if _module ^= "CLAB" then module = _module;
    moduleo = _module_o;
    SPCANDTC = _SPCANDTC;
    LINE = _LINE;
/*     BCBMDTC = _BCBMDTC; */
/*     BMSLOC = _BMSLOC; */
run;

/* To derive EPOCH  */
 %sdtm_epoch(indata=lb1, outdata=lb2, domain= lb, debug=N); 

/* To derive VISIT  */
 %sdtm_visit(indata = lb2, outdata=lb3); 
data lb3;
    set lb3;
    visitn = visitnum;
run;

option mprint mlogic symbolgen;
/* To derive --SEQ  */
 %sdtm_seq(indata=lb3, domain=lb); 
  
/* To derive Baseline Flag for Findings Domains  */
 %sdtm_blfl(domain = lb, indata = lb3, outdata = lb3 , sortby=studyid usubjid &domain.dtc &domain.cat &domain.spid &domain.testcd &domain.stresu SPCANDTC, 
            groupvar=&domain.cat &domain.spid, debug = N); 
 %sdtm_lobxfl(domain = lb, indata = lb3, outdata = lb3 , sortby=studyid usubjid &domain.testcd &domain.dtc &domain.spid &domain.testcd &domain.stresu SPCANDTC, 
            groupvar=&domain.cat &domain.spid, debug = N); 
  
/* Step 4: Create Main Domain Dataset */
***final dataset****;
%sdtm_rescrn(dsin=lb3, dsout=final_sdtm, debug=N);

%let nobs=%count_obs(indata=final_sdtm);
%if &nobs ne 0 %then
    %do;
    ***final SDTM dataset****;
    %sdtm_build(domain=&pgmname.,indata=final_sdtm,outdata=SDTM.&pgmname.); 
    %end;

/* Step 5: Create Supp-- Dataset */
%sdtm_suppxx(domain =&pgmname., indata =final_sdtm , outdata =final_supp , 
                qeval_condi = if qorig='Assigned' then qeval = 'SPONSOR', debug=Y);

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

**************************************************************************;
* End of Programming
**************************************************************************;
%logcheck_indi;

