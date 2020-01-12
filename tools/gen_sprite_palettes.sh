#!/bin/bash

my_dir=$(dirname $(readlink -f $0))

pal_sz="0x20"
pal_offsets="0x11259E 0x0D9400 0x0D9820 0x0D9840 0x0D9860 0x0D9880 0x0D98A0 0x0D98C0 0x0D98E0 0x0D9900 0x0D9B20 0x0D9B40 0x0D9B60 0x0D9B80 0x0D9BA0 0x0D9BC0 0x0D9BE0 0x0D9C00 0x0D9C20 0x0D9C40 0x0D9C60 0x0D9C80 0x0D9CA0 0x0D9CC0 0x0D9CE0 0x0D9D00 0x6DB6B  0x6DBBA  0x6DC09  0x6DC58  0x6DCA4 0x6E466  0x6E488  0x6E4AA  0x6E4CC  0x6E4EE  0x6E510  0x6E532  0x6E554  0x6E576  0x6E598  0x6E5BA  0x6E5DC  0x6E5FE  0x6E620  0x6E642  0x6E664 0x6DB8F 0x6DC2D 0x6DC7C 0x6DBDE 0x0D9520 0x0D9920 0x0D9940 0x0D9960 0x0D9980 0x0D99A0 0x0D99C0 0x0D99E0 0x0D9A00 0x0D9D20 0x0D9D40 0x0D9D60 0x0D9D80 0x0D9DA0 0x0D9DC0 0x0D9DE0 0x0D9E00 0x0D9E20 0x0D9E40 0x0D9E60 0x0D9E80 0x0D9EA0 0x0D9EC0 0x0D9EE0 0x0D9F00 0x6DCD1  0x6DD20  0x6DD6F  0x6DDBE  0x6DE0A 0x6E692  0x6E6B4  0x6E6D6  0x6E6F8  0x6E71A  0x6E73C  0x6E75E  0x6E780  0x6E7A2  0x6E7C4  0x6E7E6  0x6E808  0x6E82A  0x6E84C  0x6E86E  0x6E890 0x6DCF5 0x6DD44 0x6DD93 0x6DDE2 0x0D9540 0x0D9560 0x0D9580 0x0D95A0 0x0D95C0 0x0D95E0 0x0D9600 0x0D9620 0x0D9640 0x0D9660 0x0D9680 0x0D96A0 0x0D9780 0x0D97A0 0x0D97C0 0x0D97E0 0x0D9800 0x0D9A20 0x0D9A40 0x0D9A60 0x0D9A80 0x0D9AA0 0x0D9AC0 0x0D9AE0 0x0D9B00 0x0D9F20 0x0D9F40 0x0D9F60 0x0D9F80 0x0D9FA0 0x0D9FC0 0x0D9FE0 0x0DA000 0x0DA020 0x0DA040 0x0DA060 0x0DA080 0x0DA0A0 0x0DA0C0 0x0DA0E0 0x0DA100 0x6DE37  0x6DE86  0x6DED5  0x6DF24  0x6DF70 0x6E8BE  0x6E8E0  0x6E902  0x6E924  0x6E946  0x6E968  0x6E98A  0x6E9AC  0x6E9CE  0x6E9F0  0x6EA12  0x6EA34  0x6EA56  0x6EA78  0x6EA9A  0x6EABC 0x6DE5B 0x6DEAA 0x6DEF9 0x6DF48"
sprite_palletes_file=$1
if [ -z "$sprite_palletes_file" ]; then
    sprite_palletes_file=${my_dir}/../itemrandomizerweb/sprite_palettes.py
else
    shift
fi
roms=$*
[ -z "$roms" ] && roms=${my_dir}/../sprite_roms/*.sfc
[ ! -s "$sprite_palletes_file" ] && echo "sprite_palettes = {}" > $sprite_palletes_file

for sprite_file in $roms; do
    sprite="$(basename $sprite_file sfc)ips"
    echo $sprite
    printf "sprite_palettes['%s'] = {\n" $sprite >> $sprite_palletes_file
    for off in $pal_offsets; do
	${my_dir}/extract_data.py $sprite_file $off $pal_sz >> $sprite_palletes_file
    done
    echo "}" >> $sprite_palletes_file
done
