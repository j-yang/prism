/**************************update 1: to add setup******************************/
%setup(version=260,
	   localsetup=root/cdar/%scan(&_exec_programpath.,3,/)/%scan(&_exec_programpath.,4,/)/ar/%scan(&_exec_programpath.,6,/)/common/%scan(&_exec_programpath.,8,/)/macro/localsetup.sas);

%localsetup;

proc datasets nolist memtype=data library=work kill;;
run;


%macro sdtm_shell(domain=);
/*----------------------------------------------------------------------------*/
/*--------------Read in spec, generate meta for SDTM domains------------------*/
/*-----------------------------------------------------------------------------*/
proc import  out=CONTENT(where=(SDTM_Domain_Description ne '')) 
  datafile="&sdtm_spec"
  dbms=xlsx replace;
  range="CONTENT$A6:H";
run;

data sdtm_content ;
  set CONTENT ;
  Sort_Order=tranwrd(Sort_Order, ',',' '); 
  SDTM_Domain=upcase(SDTM_Domain); 

  keep SDTM_Domain Sort_Order  SDTM_Domain_Description;
  rename SDTM_Domain = Domain Sort_Order = order SDTM_Domain_Description =label;
run;

data meta.meta_sdtm;
  set sdtm_content;
run;

/*----------------------------------------------------------------------------*/
/*--------------Read in spec, generate shell for each SDTM domain------------------*/
/*-----------------------------------------------------------------------------*/

proc import out=spec(rename=(Variable_Name=NAME Variable_Label=LABEL)) 
  datafile="&sdtm_spec"
  dbms=xlsx replace;
  range="&domain$A13:J";
run;

data spec1;
  length typea $10.;
  /*Change to exclude supp domain variables from spec 2022-01-04   kjcj731 */
  set spec(where =(name not in('',"CONTENT") and upcase(strip(Variable_Type)) ne "SUPP"));
/* set spec(where =(name not in('',"CONTENT") and Drop = '' ));     */
/*Change to exclude supp domain variables from spec  2022-01-04   kjcj731 */
  if find(name,':')=0;
  if not missing(length) then length_=compress('('||put(length,best.)||')');
  if  compress(type) = 'C' then typea = 'CHAR';
  if  compress(type) = 'N' then typea = 'NUM';
  tylen=cats(typea,length_);
  keep NAME TYLEN LABEL Variable_Order;
run;

data _null_;
  set spec1 end=eof;
/*  where name not like '__SEQ'; */
  call symputx(compress("cname"||put(_N_,best.)),name);
  call symputx(compress("clabel"||put(_N_,best.)),label);
  call symputx(compress("ctylen"||put(_N_,best.)),tylen);
  if eof then call symputx("num",_N_);
run;

proc sql;
  create table templet
  ( 
  %do i=1 %to &num;
  &&cname&i &&ctylen&i label="&&clabel&i"
  %if &i<&num %then %str(,);
  %else %str();
  %end;
  );
quit;

data meta.meta_&domain.;
  set spec1;
  keep NAME LABEL;
  rename name = variable ; 
run;


data meta.shell_&domain.;
set templet;
run;

proc datasets lib=work memtype=data nolist;
  delete  spec spec1 templet sdtm_content content;
quit;

%mend sdtm_shell;

%sdtm_shell(domain=ae);
%sdtm_shell(domain=ce);
%sdtm_shell(domain=cm);
%sdtm_shell(domain=co);
%sdtm_shell(domain=cv);
%sdtm_shell(domain=dm);
%sdtm_shell(domain=dd);
%sdtm_shell(domain=ds);
%sdtm_shell(domain=dv);
%sdtm_shell(domain=ec);
%sdtm_shell(domain=ex);
%sdtm_shell(domain=eg);
%sdtm_shell(domain=fa);
%*sdtm_shell(domain=face);
%*sdtm_shell(domain=faho);
%*sdtm_shell(domain=faae);
%sdtm_shell(domain=ft);
%sdtm_shell(domain=ho);
%sdtm_shell(domain=ie);
%sdtm_shell(domain=lb);
%sdtm_shell(domain=mi);
%sdtm_shell(domain=mh);
%sdtm_shell(domain=oe);
%sdtm_shell(domain=pc);
%sdtm_shell(domain=pr);
%sdtm_shell(domain=qs);
%sdtm_shell(domain=rp);
%sdtm_shell(domain=se);
%sdtm_shell(domain=sv);
%sdtm_shell(domain=ta);
%sdtm_shell(domain=te);
%sdtm_shell(domain=ti);
%sdtm_shell(domain=ts);
%sdtm_shell(domain=tv);
%sdtm_shell(domain=vs);



