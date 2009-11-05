/*****************************************************************************
 * Project: RooFit                                                           *
 *                                                                           *
  * This code was autogenerated by RooClassFactory                            * 
 *****************************************************************************/

#ifndef _MGMWimpTimeFunction_hh_
#define _MGMWimpTimeFunction_hh_

#include "RooAbsReal.h"
#include "RooRealProxy.h"
#include "RooCategoryProxy.h"
#include "RooAbsReal.h"
#include "RooAbsCategory.h"
 
class MGMWimpTimeFunction : public RooAbsReal {
public:
  MGMWimpTimeFunction() {} ; 
  MGMWimpTimeFunction(const char *name, const char *title,
	      RooAbsReal& _velocity_0,
	      RooAbsReal& _velocity_1,
	      RooAbsReal& _time);
  MGMWimpTimeFunction(const MGMWimpTimeFunction& other, const char* name=0) ;
  virtual TObject* clone(const char* newname) const { return new MGMWimpTimeFunction(*this,newname); }
  inline virtual ~MGMWimpTimeFunction() { }

protected:

  RooRealProxy velocity_0 ;
  RooRealProxy velocity_1 ;
  RooRealProxy time ;
  
  Double_t evaluate() const ;

private:

  ClassDef(MGMWimpTimeFunction,1) // Your description goes here...
};
 
#endif
