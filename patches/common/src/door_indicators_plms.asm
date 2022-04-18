;;; Define indicator PLMs for vanilla door colors. Indicators for beam doors are directly in the beam doors patch

arch snes.cpu
lorom

incsrc "doors_plms_common.asm"

;;; define vanilla color indicators here to be able to have them as a separate patch
org $84f900

%defineIndicator(missile,left)
%defineIndicator(missile,right)
%defineIndicator(missile,top)
%defineIndicator(missile,bottom)
%defineIndicator(super,left)
%defineIndicator(super,right)
%defineIndicator(super,top)
%defineIndicator(super,bottom)
%defineIndicator(PB,left)
%defineIndicator(PB,right)
%defineIndicator(PB,top)
%defineIndicator(PB,bottom)
%defineIndicatorPLM(missile,left)
%defineIndicatorPLM(missile,right)
%defineIndicatorPLM(missile,top)
%defineIndicatorPLM(missile,bottom)
%defineIndicatorPLM(super,left)
%defineIndicatorPLM(super,right)
%defineIndicatorPLM(super,top)
%defineIndicatorPLM(super,bottom)
%defineIndicatorPLM(PB,left)
%defineIndicatorPLM(PB,right)
%defineIndicatorPLM(PB,top)
%defineIndicatorPLM(PB,bottom)

print "bank 84 end: ", pc
warnpc $84fbff
