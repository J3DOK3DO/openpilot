#include "pose.h"

namespace {
#define DIM 18
#define EDIM 18
#define MEDIM 18
typedef void (*Hfun)(double *, double *, double *);
const static double MAHA_THRESH_4 = 7.814727903251177;
const static double MAHA_THRESH_10 = 7.814727903251177;
const static double MAHA_THRESH_13 = 7.814727903251177;
const static double MAHA_THRESH_14 = 7.814727903251177;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_671460305092226609) {
   out_671460305092226609[0] = delta_x[0] + nom_x[0];
   out_671460305092226609[1] = delta_x[1] + nom_x[1];
   out_671460305092226609[2] = delta_x[2] + nom_x[2];
   out_671460305092226609[3] = delta_x[3] + nom_x[3];
   out_671460305092226609[4] = delta_x[4] + nom_x[4];
   out_671460305092226609[5] = delta_x[5] + nom_x[5];
   out_671460305092226609[6] = delta_x[6] + nom_x[6];
   out_671460305092226609[7] = delta_x[7] + nom_x[7];
   out_671460305092226609[8] = delta_x[8] + nom_x[8];
   out_671460305092226609[9] = delta_x[9] + nom_x[9];
   out_671460305092226609[10] = delta_x[10] + nom_x[10];
   out_671460305092226609[11] = delta_x[11] + nom_x[11];
   out_671460305092226609[12] = delta_x[12] + nom_x[12];
   out_671460305092226609[13] = delta_x[13] + nom_x[13];
   out_671460305092226609[14] = delta_x[14] + nom_x[14];
   out_671460305092226609[15] = delta_x[15] + nom_x[15];
   out_671460305092226609[16] = delta_x[16] + nom_x[16];
   out_671460305092226609[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_8594657692984849886) {
   out_8594657692984849886[0] = -nom_x[0] + true_x[0];
   out_8594657692984849886[1] = -nom_x[1] + true_x[1];
   out_8594657692984849886[2] = -nom_x[2] + true_x[2];
   out_8594657692984849886[3] = -nom_x[3] + true_x[3];
   out_8594657692984849886[4] = -nom_x[4] + true_x[4];
   out_8594657692984849886[5] = -nom_x[5] + true_x[5];
   out_8594657692984849886[6] = -nom_x[6] + true_x[6];
   out_8594657692984849886[7] = -nom_x[7] + true_x[7];
   out_8594657692984849886[8] = -nom_x[8] + true_x[8];
   out_8594657692984849886[9] = -nom_x[9] + true_x[9];
   out_8594657692984849886[10] = -nom_x[10] + true_x[10];
   out_8594657692984849886[11] = -nom_x[11] + true_x[11];
   out_8594657692984849886[12] = -nom_x[12] + true_x[12];
   out_8594657692984849886[13] = -nom_x[13] + true_x[13];
   out_8594657692984849886[14] = -nom_x[14] + true_x[14];
   out_8594657692984849886[15] = -nom_x[15] + true_x[15];
   out_8594657692984849886[16] = -nom_x[16] + true_x[16];
   out_8594657692984849886[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_6213728924716372500) {
   out_6213728924716372500[0] = 1.0;
   out_6213728924716372500[1] = 0.0;
   out_6213728924716372500[2] = 0.0;
   out_6213728924716372500[3] = 0.0;
   out_6213728924716372500[4] = 0.0;
   out_6213728924716372500[5] = 0.0;
   out_6213728924716372500[6] = 0.0;
   out_6213728924716372500[7] = 0.0;
   out_6213728924716372500[8] = 0.0;
   out_6213728924716372500[9] = 0.0;
   out_6213728924716372500[10] = 0.0;
   out_6213728924716372500[11] = 0.0;
   out_6213728924716372500[12] = 0.0;
   out_6213728924716372500[13] = 0.0;
   out_6213728924716372500[14] = 0.0;
   out_6213728924716372500[15] = 0.0;
   out_6213728924716372500[16] = 0.0;
   out_6213728924716372500[17] = 0.0;
   out_6213728924716372500[18] = 0.0;
   out_6213728924716372500[19] = 1.0;
   out_6213728924716372500[20] = 0.0;
   out_6213728924716372500[21] = 0.0;
   out_6213728924716372500[22] = 0.0;
   out_6213728924716372500[23] = 0.0;
   out_6213728924716372500[24] = 0.0;
   out_6213728924716372500[25] = 0.0;
   out_6213728924716372500[26] = 0.0;
   out_6213728924716372500[27] = 0.0;
   out_6213728924716372500[28] = 0.0;
   out_6213728924716372500[29] = 0.0;
   out_6213728924716372500[30] = 0.0;
   out_6213728924716372500[31] = 0.0;
   out_6213728924716372500[32] = 0.0;
   out_6213728924716372500[33] = 0.0;
   out_6213728924716372500[34] = 0.0;
   out_6213728924716372500[35] = 0.0;
   out_6213728924716372500[36] = 0.0;
   out_6213728924716372500[37] = 0.0;
   out_6213728924716372500[38] = 1.0;
   out_6213728924716372500[39] = 0.0;
   out_6213728924716372500[40] = 0.0;
   out_6213728924716372500[41] = 0.0;
   out_6213728924716372500[42] = 0.0;
   out_6213728924716372500[43] = 0.0;
   out_6213728924716372500[44] = 0.0;
   out_6213728924716372500[45] = 0.0;
   out_6213728924716372500[46] = 0.0;
   out_6213728924716372500[47] = 0.0;
   out_6213728924716372500[48] = 0.0;
   out_6213728924716372500[49] = 0.0;
   out_6213728924716372500[50] = 0.0;
   out_6213728924716372500[51] = 0.0;
   out_6213728924716372500[52] = 0.0;
   out_6213728924716372500[53] = 0.0;
   out_6213728924716372500[54] = 0.0;
   out_6213728924716372500[55] = 0.0;
   out_6213728924716372500[56] = 0.0;
   out_6213728924716372500[57] = 1.0;
   out_6213728924716372500[58] = 0.0;
   out_6213728924716372500[59] = 0.0;
   out_6213728924716372500[60] = 0.0;
   out_6213728924716372500[61] = 0.0;
   out_6213728924716372500[62] = 0.0;
   out_6213728924716372500[63] = 0.0;
   out_6213728924716372500[64] = 0.0;
   out_6213728924716372500[65] = 0.0;
   out_6213728924716372500[66] = 0.0;
   out_6213728924716372500[67] = 0.0;
   out_6213728924716372500[68] = 0.0;
   out_6213728924716372500[69] = 0.0;
   out_6213728924716372500[70] = 0.0;
   out_6213728924716372500[71] = 0.0;
   out_6213728924716372500[72] = 0.0;
   out_6213728924716372500[73] = 0.0;
   out_6213728924716372500[74] = 0.0;
   out_6213728924716372500[75] = 0.0;
   out_6213728924716372500[76] = 1.0;
   out_6213728924716372500[77] = 0.0;
   out_6213728924716372500[78] = 0.0;
   out_6213728924716372500[79] = 0.0;
   out_6213728924716372500[80] = 0.0;
   out_6213728924716372500[81] = 0.0;
   out_6213728924716372500[82] = 0.0;
   out_6213728924716372500[83] = 0.0;
   out_6213728924716372500[84] = 0.0;
   out_6213728924716372500[85] = 0.0;
   out_6213728924716372500[86] = 0.0;
   out_6213728924716372500[87] = 0.0;
   out_6213728924716372500[88] = 0.0;
   out_6213728924716372500[89] = 0.0;
   out_6213728924716372500[90] = 0.0;
   out_6213728924716372500[91] = 0.0;
   out_6213728924716372500[92] = 0.0;
   out_6213728924716372500[93] = 0.0;
   out_6213728924716372500[94] = 0.0;
   out_6213728924716372500[95] = 1.0;
   out_6213728924716372500[96] = 0.0;
   out_6213728924716372500[97] = 0.0;
   out_6213728924716372500[98] = 0.0;
   out_6213728924716372500[99] = 0.0;
   out_6213728924716372500[100] = 0.0;
   out_6213728924716372500[101] = 0.0;
   out_6213728924716372500[102] = 0.0;
   out_6213728924716372500[103] = 0.0;
   out_6213728924716372500[104] = 0.0;
   out_6213728924716372500[105] = 0.0;
   out_6213728924716372500[106] = 0.0;
   out_6213728924716372500[107] = 0.0;
   out_6213728924716372500[108] = 0.0;
   out_6213728924716372500[109] = 0.0;
   out_6213728924716372500[110] = 0.0;
   out_6213728924716372500[111] = 0.0;
   out_6213728924716372500[112] = 0.0;
   out_6213728924716372500[113] = 0.0;
   out_6213728924716372500[114] = 1.0;
   out_6213728924716372500[115] = 0.0;
   out_6213728924716372500[116] = 0.0;
   out_6213728924716372500[117] = 0.0;
   out_6213728924716372500[118] = 0.0;
   out_6213728924716372500[119] = 0.0;
   out_6213728924716372500[120] = 0.0;
   out_6213728924716372500[121] = 0.0;
   out_6213728924716372500[122] = 0.0;
   out_6213728924716372500[123] = 0.0;
   out_6213728924716372500[124] = 0.0;
   out_6213728924716372500[125] = 0.0;
   out_6213728924716372500[126] = 0.0;
   out_6213728924716372500[127] = 0.0;
   out_6213728924716372500[128] = 0.0;
   out_6213728924716372500[129] = 0.0;
   out_6213728924716372500[130] = 0.0;
   out_6213728924716372500[131] = 0.0;
   out_6213728924716372500[132] = 0.0;
   out_6213728924716372500[133] = 1.0;
   out_6213728924716372500[134] = 0.0;
   out_6213728924716372500[135] = 0.0;
   out_6213728924716372500[136] = 0.0;
   out_6213728924716372500[137] = 0.0;
   out_6213728924716372500[138] = 0.0;
   out_6213728924716372500[139] = 0.0;
   out_6213728924716372500[140] = 0.0;
   out_6213728924716372500[141] = 0.0;
   out_6213728924716372500[142] = 0.0;
   out_6213728924716372500[143] = 0.0;
   out_6213728924716372500[144] = 0.0;
   out_6213728924716372500[145] = 0.0;
   out_6213728924716372500[146] = 0.0;
   out_6213728924716372500[147] = 0.0;
   out_6213728924716372500[148] = 0.0;
   out_6213728924716372500[149] = 0.0;
   out_6213728924716372500[150] = 0.0;
   out_6213728924716372500[151] = 0.0;
   out_6213728924716372500[152] = 1.0;
   out_6213728924716372500[153] = 0.0;
   out_6213728924716372500[154] = 0.0;
   out_6213728924716372500[155] = 0.0;
   out_6213728924716372500[156] = 0.0;
   out_6213728924716372500[157] = 0.0;
   out_6213728924716372500[158] = 0.0;
   out_6213728924716372500[159] = 0.0;
   out_6213728924716372500[160] = 0.0;
   out_6213728924716372500[161] = 0.0;
   out_6213728924716372500[162] = 0.0;
   out_6213728924716372500[163] = 0.0;
   out_6213728924716372500[164] = 0.0;
   out_6213728924716372500[165] = 0.0;
   out_6213728924716372500[166] = 0.0;
   out_6213728924716372500[167] = 0.0;
   out_6213728924716372500[168] = 0.0;
   out_6213728924716372500[169] = 0.0;
   out_6213728924716372500[170] = 0.0;
   out_6213728924716372500[171] = 1.0;
   out_6213728924716372500[172] = 0.0;
   out_6213728924716372500[173] = 0.0;
   out_6213728924716372500[174] = 0.0;
   out_6213728924716372500[175] = 0.0;
   out_6213728924716372500[176] = 0.0;
   out_6213728924716372500[177] = 0.0;
   out_6213728924716372500[178] = 0.0;
   out_6213728924716372500[179] = 0.0;
   out_6213728924716372500[180] = 0.0;
   out_6213728924716372500[181] = 0.0;
   out_6213728924716372500[182] = 0.0;
   out_6213728924716372500[183] = 0.0;
   out_6213728924716372500[184] = 0.0;
   out_6213728924716372500[185] = 0.0;
   out_6213728924716372500[186] = 0.0;
   out_6213728924716372500[187] = 0.0;
   out_6213728924716372500[188] = 0.0;
   out_6213728924716372500[189] = 0.0;
   out_6213728924716372500[190] = 1.0;
   out_6213728924716372500[191] = 0.0;
   out_6213728924716372500[192] = 0.0;
   out_6213728924716372500[193] = 0.0;
   out_6213728924716372500[194] = 0.0;
   out_6213728924716372500[195] = 0.0;
   out_6213728924716372500[196] = 0.0;
   out_6213728924716372500[197] = 0.0;
   out_6213728924716372500[198] = 0.0;
   out_6213728924716372500[199] = 0.0;
   out_6213728924716372500[200] = 0.0;
   out_6213728924716372500[201] = 0.0;
   out_6213728924716372500[202] = 0.0;
   out_6213728924716372500[203] = 0.0;
   out_6213728924716372500[204] = 0.0;
   out_6213728924716372500[205] = 0.0;
   out_6213728924716372500[206] = 0.0;
   out_6213728924716372500[207] = 0.0;
   out_6213728924716372500[208] = 0.0;
   out_6213728924716372500[209] = 1.0;
   out_6213728924716372500[210] = 0.0;
   out_6213728924716372500[211] = 0.0;
   out_6213728924716372500[212] = 0.0;
   out_6213728924716372500[213] = 0.0;
   out_6213728924716372500[214] = 0.0;
   out_6213728924716372500[215] = 0.0;
   out_6213728924716372500[216] = 0.0;
   out_6213728924716372500[217] = 0.0;
   out_6213728924716372500[218] = 0.0;
   out_6213728924716372500[219] = 0.0;
   out_6213728924716372500[220] = 0.0;
   out_6213728924716372500[221] = 0.0;
   out_6213728924716372500[222] = 0.0;
   out_6213728924716372500[223] = 0.0;
   out_6213728924716372500[224] = 0.0;
   out_6213728924716372500[225] = 0.0;
   out_6213728924716372500[226] = 0.0;
   out_6213728924716372500[227] = 0.0;
   out_6213728924716372500[228] = 1.0;
   out_6213728924716372500[229] = 0.0;
   out_6213728924716372500[230] = 0.0;
   out_6213728924716372500[231] = 0.0;
   out_6213728924716372500[232] = 0.0;
   out_6213728924716372500[233] = 0.0;
   out_6213728924716372500[234] = 0.0;
   out_6213728924716372500[235] = 0.0;
   out_6213728924716372500[236] = 0.0;
   out_6213728924716372500[237] = 0.0;
   out_6213728924716372500[238] = 0.0;
   out_6213728924716372500[239] = 0.0;
   out_6213728924716372500[240] = 0.0;
   out_6213728924716372500[241] = 0.0;
   out_6213728924716372500[242] = 0.0;
   out_6213728924716372500[243] = 0.0;
   out_6213728924716372500[244] = 0.0;
   out_6213728924716372500[245] = 0.0;
   out_6213728924716372500[246] = 0.0;
   out_6213728924716372500[247] = 1.0;
   out_6213728924716372500[248] = 0.0;
   out_6213728924716372500[249] = 0.0;
   out_6213728924716372500[250] = 0.0;
   out_6213728924716372500[251] = 0.0;
   out_6213728924716372500[252] = 0.0;
   out_6213728924716372500[253] = 0.0;
   out_6213728924716372500[254] = 0.0;
   out_6213728924716372500[255] = 0.0;
   out_6213728924716372500[256] = 0.0;
   out_6213728924716372500[257] = 0.0;
   out_6213728924716372500[258] = 0.0;
   out_6213728924716372500[259] = 0.0;
   out_6213728924716372500[260] = 0.0;
   out_6213728924716372500[261] = 0.0;
   out_6213728924716372500[262] = 0.0;
   out_6213728924716372500[263] = 0.0;
   out_6213728924716372500[264] = 0.0;
   out_6213728924716372500[265] = 0.0;
   out_6213728924716372500[266] = 1.0;
   out_6213728924716372500[267] = 0.0;
   out_6213728924716372500[268] = 0.0;
   out_6213728924716372500[269] = 0.0;
   out_6213728924716372500[270] = 0.0;
   out_6213728924716372500[271] = 0.0;
   out_6213728924716372500[272] = 0.0;
   out_6213728924716372500[273] = 0.0;
   out_6213728924716372500[274] = 0.0;
   out_6213728924716372500[275] = 0.0;
   out_6213728924716372500[276] = 0.0;
   out_6213728924716372500[277] = 0.0;
   out_6213728924716372500[278] = 0.0;
   out_6213728924716372500[279] = 0.0;
   out_6213728924716372500[280] = 0.0;
   out_6213728924716372500[281] = 0.0;
   out_6213728924716372500[282] = 0.0;
   out_6213728924716372500[283] = 0.0;
   out_6213728924716372500[284] = 0.0;
   out_6213728924716372500[285] = 1.0;
   out_6213728924716372500[286] = 0.0;
   out_6213728924716372500[287] = 0.0;
   out_6213728924716372500[288] = 0.0;
   out_6213728924716372500[289] = 0.0;
   out_6213728924716372500[290] = 0.0;
   out_6213728924716372500[291] = 0.0;
   out_6213728924716372500[292] = 0.0;
   out_6213728924716372500[293] = 0.0;
   out_6213728924716372500[294] = 0.0;
   out_6213728924716372500[295] = 0.0;
   out_6213728924716372500[296] = 0.0;
   out_6213728924716372500[297] = 0.0;
   out_6213728924716372500[298] = 0.0;
   out_6213728924716372500[299] = 0.0;
   out_6213728924716372500[300] = 0.0;
   out_6213728924716372500[301] = 0.0;
   out_6213728924716372500[302] = 0.0;
   out_6213728924716372500[303] = 0.0;
   out_6213728924716372500[304] = 1.0;
   out_6213728924716372500[305] = 0.0;
   out_6213728924716372500[306] = 0.0;
   out_6213728924716372500[307] = 0.0;
   out_6213728924716372500[308] = 0.0;
   out_6213728924716372500[309] = 0.0;
   out_6213728924716372500[310] = 0.0;
   out_6213728924716372500[311] = 0.0;
   out_6213728924716372500[312] = 0.0;
   out_6213728924716372500[313] = 0.0;
   out_6213728924716372500[314] = 0.0;
   out_6213728924716372500[315] = 0.0;
   out_6213728924716372500[316] = 0.0;
   out_6213728924716372500[317] = 0.0;
   out_6213728924716372500[318] = 0.0;
   out_6213728924716372500[319] = 0.0;
   out_6213728924716372500[320] = 0.0;
   out_6213728924716372500[321] = 0.0;
   out_6213728924716372500[322] = 0.0;
   out_6213728924716372500[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_5585784149500665013) {
   out_5585784149500665013[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_5585784149500665013[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_5585784149500665013[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_5585784149500665013[3] = dt*state[12] + state[3];
   out_5585784149500665013[4] = dt*state[13] + state[4];
   out_5585784149500665013[5] = dt*state[14] + state[5];
   out_5585784149500665013[6] = state[6];
   out_5585784149500665013[7] = state[7];
   out_5585784149500665013[8] = state[8];
   out_5585784149500665013[9] = state[9];
   out_5585784149500665013[10] = state[10];
   out_5585784149500665013[11] = state[11];
   out_5585784149500665013[12] = state[12];
   out_5585784149500665013[13] = state[13];
   out_5585784149500665013[14] = state[14];
   out_5585784149500665013[15] = state[15];
   out_5585784149500665013[16] = state[16];
   out_5585784149500665013[17] = state[17];
}
void F_fun(double *state, double dt, double *out_3643040962092382423) {
   out_3643040962092382423[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3643040962092382423[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3643040962092382423[2] = 0;
   out_3643040962092382423[3] = 0;
   out_3643040962092382423[4] = 0;
   out_3643040962092382423[5] = 0;
   out_3643040962092382423[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3643040962092382423[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3643040962092382423[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_3643040962092382423[9] = 0;
   out_3643040962092382423[10] = 0;
   out_3643040962092382423[11] = 0;
   out_3643040962092382423[12] = 0;
   out_3643040962092382423[13] = 0;
   out_3643040962092382423[14] = 0;
   out_3643040962092382423[15] = 0;
   out_3643040962092382423[16] = 0;
   out_3643040962092382423[17] = 0;
   out_3643040962092382423[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3643040962092382423[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3643040962092382423[20] = 0;
   out_3643040962092382423[21] = 0;
   out_3643040962092382423[22] = 0;
   out_3643040962092382423[23] = 0;
   out_3643040962092382423[24] = 0;
   out_3643040962092382423[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3643040962092382423[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_3643040962092382423[27] = 0;
   out_3643040962092382423[28] = 0;
   out_3643040962092382423[29] = 0;
   out_3643040962092382423[30] = 0;
   out_3643040962092382423[31] = 0;
   out_3643040962092382423[32] = 0;
   out_3643040962092382423[33] = 0;
   out_3643040962092382423[34] = 0;
   out_3643040962092382423[35] = 0;
   out_3643040962092382423[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3643040962092382423[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3643040962092382423[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3643040962092382423[39] = 0;
   out_3643040962092382423[40] = 0;
   out_3643040962092382423[41] = 0;
   out_3643040962092382423[42] = 0;
   out_3643040962092382423[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3643040962092382423[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_3643040962092382423[45] = 0;
   out_3643040962092382423[46] = 0;
   out_3643040962092382423[47] = 0;
   out_3643040962092382423[48] = 0;
   out_3643040962092382423[49] = 0;
   out_3643040962092382423[50] = 0;
   out_3643040962092382423[51] = 0;
   out_3643040962092382423[52] = 0;
   out_3643040962092382423[53] = 0;
   out_3643040962092382423[54] = 0;
   out_3643040962092382423[55] = 0;
   out_3643040962092382423[56] = 0;
   out_3643040962092382423[57] = 1;
   out_3643040962092382423[58] = 0;
   out_3643040962092382423[59] = 0;
   out_3643040962092382423[60] = 0;
   out_3643040962092382423[61] = 0;
   out_3643040962092382423[62] = 0;
   out_3643040962092382423[63] = 0;
   out_3643040962092382423[64] = 0;
   out_3643040962092382423[65] = 0;
   out_3643040962092382423[66] = dt;
   out_3643040962092382423[67] = 0;
   out_3643040962092382423[68] = 0;
   out_3643040962092382423[69] = 0;
   out_3643040962092382423[70] = 0;
   out_3643040962092382423[71] = 0;
   out_3643040962092382423[72] = 0;
   out_3643040962092382423[73] = 0;
   out_3643040962092382423[74] = 0;
   out_3643040962092382423[75] = 0;
   out_3643040962092382423[76] = 1;
   out_3643040962092382423[77] = 0;
   out_3643040962092382423[78] = 0;
   out_3643040962092382423[79] = 0;
   out_3643040962092382423[80] = 0;
   out_3643040962092382423[81] = 0;
   out_3643040962092382423[82] = 0;
   out_3643040962092382423[83] = 0;
   out_3643040962092382423[84] = 0;
   out_3643040962092382423[85] = dt;
   out_3643040962092382423[86] = 0;
   out_3643040962092382423[87] = 0;
   out_3643040962092382423[88] = 0;
   out_3643040962092382423[89] = 0;
   out_3643040962092382423[90] = 0;
   out_3643040962092382423[91] = 0;
   out_3643040962092382423[92] = 0;
   out_3643040962092382423[93] = 0;
   out_3643040962092382423[94] = 0;
   out_3643040962092382423[95] = 1;
   out_3643040962092382423[96] = 0;
   out_3643040962092382423[97] = 0;
   out_3643040962092382423[98] = 0;
   out_3643040962092382423[99] = 0;
   out_3643040962092382423[100] = 0;
   out_3643040962092382423[101] = 0;
   out_3643040962092382423[102] = 0;
   out_3643040962092382423[103] = 0;
   out_3643040962092382423[104] = dt;
   out_3643040962092382423[105] = 0;
   out_3643040962092382423[106] = 0;
   out_3643040962092382423[107] = 0;
   out_3643040962092382423[108] = 0;
   out_3643040962092382423[109] = 0;
   out_3643040962092382423[110] = 0;
   out_3643040962092382423[111] = 0;
   out_3643040962092382423[112] = 0;
   out_3643040962092382423[113] = 0;
   out_3643040962092382423[114] = 1;
   out_3643040962092382423[115] = 0;
   out_3643040962092382423[116] = 0;
   out_3643040962092382423[117] = 0;
   out_3643040962092382423[118] = 0;
   out_3643040962092382423[119] = 0;
   out_3643040962092382423[120] = 0;
   out_3643040962092382423[121] = 0;
   out_3643040962092382423[122] = 0;
   out_3643040962092382423[123] = 0;
   out_3643040962092382423[124] = 0;
   out_3643040962092382423[125] = 0;
   out_3643040962092382423[126] = 0;
   out_3643040962092382423[127] = 0;
   out_3643040962092382423[128] = 0;
   out_3643040962092382423[129] = 0;
   out_3643040962092382423[130] = 0;
   out_3643040962092382423[131] = 0;
   out_3643040962092382423[132] = 0;
   out_3643040962092382423[133] = 1;
   out_3643040962092382423[134] = 0;
   out_3643040962092382423[135] = 0;
   out_3643040962092382423[136] = 0;
   out_3643040962092382423[137] = 0;
   out_3643040962092382423[138] = 0;
   out_3643040962092382423[139] = 0;
   out_3643040962092382423[140] = 0;
   out_3643040962092382423[141] = 0;
   out_3643040962092382423[142] = 0;
   out_3643040962092382423[143] = 0;
   out_3643040962092382423[144] = 0;
   out_3643040962092382423[145] = 0;
   out_3643040962092382423[146] = 0;
   out_3643040962092382423[147] = 0;
   out_3643040962092382423[148] = 0;
   out_3643040962092382423[149] = 0;
   out_3643040962092382423[150] = 0;
   out_3643040962092382423[151] = 0;
   out_3643040962092382423[152] = 1;
   out_3643040962092382423[153] = 0;
   out_3643040962092382423[154] = 0;
   out_3643040962092382423[155] = 0;
   out_3643040962092382423[156] = 0;
   out_3643040962092382423[157] = 0;
   out_3643040962092382423[158] = 0;
   out_3643040962092382423[159] = 0;
   out_3643040962092382423[160] = 0;
   out_3643040962092382423[161] = 0;
   out_3643040962092382423[162] = 0;
   out_3643040962092382423[163] = 0;
   out_3643040962092382423[164] = 0;
   out_3643040962092382423[165] = 0;
   out_3643040962092382423[166] = 0;
   out_3643040962092382423[167] = 0;
   out_3643040962092382423[168] = 0;
   out_3643040962092382423[169] = 0;
   out_3643040962092382423[170] = 0;
   out_3643040962092382423[171] = 1;
   out_3643040962092382423[172] = 0;
   out_3643040962092382423[173] = 0;
   out_3643040962092382423[174] = 0;
   out_3643040962092382423[175] = 0;
   out_3643040962092382423[176] = 0;
   out_3643040962092382423[177] = 0;
   out_3643040962092382423[178] = 0;
   out_3643040962092382423[179] = 0;
   out_3643040962092382423[180] = 0;
   out_3643040962092382423[181] = 0;
   out_3643040962092382423[182] = 0;
   out_3643040962092382423[183] = 0;
   out_3643040962092382423[184] = 0;
   out_3643040962092382423[185] = 0;
   out_3643040962092382423[186] = 0;
   out_3643040962092382423[187] = 0;
   out_3643040962092382423[188] = 0;
   out_3643040962092382423[189] = 0;
   out_3643040962092382423[190] = 1;
   out_3643040962092382423[191] = 0;
   out_3643040962092382423[192] = 0;
   out_3643040962092382423[193] = 0;
   out_3643040962092382423[194] = 0;
   out_3643040962092382423[195] = 0;
   out_3643040962092382423[196] = 0;
   out_3643040962092382423[197] = 0;
   out_3643040962092382423[198] = 0;
   out_3643040962092382423[199] = 0;
   out_3643040962092382423[200] = 0;
   out_3643040962092382423[201] = 0;
   out_3643040962092382423[202] = 0;
   out_3643040962092382423[203] = 0;
   out_3643040962092382423[204] = 0;
   out_3643040962092382423[205] = 0;
   out_3643040962092382423[206] = 0;
   out_3643040962092382423[207] = 0;
   out_3643040962092382423[208] = 0;
   out_3643040962092382423[209] = 1;
   out_3643040962092382423[210] = 0;
   out_3643040962092382423[211] = 0;
   out_3643040962092382423[212] = 0;
   out_3643040962092382423[213] = 0;
   out_3643040962092382423[214] = 0;
   out_3643040962092382423[215] = 0;
   out_3643040962092382423[216] = 0;
   out_3643040962092382423[217] = 0;
   out_3643040962092382423[218] = 0;
   out_3643040962092382423[219] = 0;
   out_3643040962092382423[220] = 0;
   out_3643040962092382423[221] = 0;
   out_3643040962092382423[222] = 0;
   out_3643040962092382423[223] = 0;
   out_3643040962092382423[224] = 0;
   out_3643040962092382423[225] = 0;
   out_3643040962092382423[226] = 0;
   out_3643040962092382423[227] = 0;
   out_3643040962092382423[228] = 1;
   out_3643040962092382423[229] = 0;
   out_3643040962092382423[230] = 0;
   out_3643040962092382423[231] = 0;
   out_3643040962092382423[232] = 0;
   out_3643040962092382423[233] = 0;
   out_3643040962092382423[234] = 0;
   out_3643040962092382423[235] = 0;
   out_3643040962092382423[236] = 0;
   out_3643040962092382423[237] = 0;
   out_3643040962092382423[238] = 0;
   out_3643040962092382423[239] = 0;
   out_3643040962092382423[240] = 0;
   out_3643040962092382423[241] = 0;
   out_3643040962092382423[242] = 0;
   out_3643040962092382423[243] = 0;
   out_3643040962092382423[244] = 0;
   out_3643040962092382423[245] = 0;
   out_3643040962092382423[246] = 0;
   out_3643040962092382423[247] = 1;
   out_3643040962092382423[248] = 0;
   out_3643040962092382423[249] = 0;
   out_3643040962092382423[250] = 0;
   out_3643040962092382423[251] = 0;
   out_3643040962092382423[252] = 0;
   out_3643040962092382423[253] = 0;
   out_3643040962092382423[254] = 0;
   out_3643040962092382423[255] = 0;
   out_3643040962092382423[256] = 0;
   out_3643040962092382423[257] = 0;
   out_3643040962092382423[258] = 0;
   out_3643040962092382423[259] = 0;
   out_3643040962092382423[260] = 0;
   out_3643040962092382423[261] = 0;
   out_3643040962092382423[262] = 0;
   out_3643040962092382423[263] = 0;
   out_3643040962092382423[264] = 0;
   out_3643040962092382423[265] = 0;
   out_3643040962092382423[266] = 1;
   out_3643040962092382423[267] = 0;
   out_3643040962092382423[268] = 0;
   out_3643040962092382423[269] = 0;
   out_3643040962092382423[270] = 0;
   out_3643040962092382423[271] = 0;
   out_3643040962092382423[272] = 0;
   out_3643040962092382423[273] = 0;
   out_3643040962092382423[274] = 0;
   out_3643040962092382423[275] = 0;
   out_3643040962092382423[276] = 0;
   out_3643040962092382423[277] = 0;
   out_3643040962092382423[278] = 0;
   out_3643040962092382423[279] = 0;
   out_3643040962092382423[280] = 0;
   out_3643040962092382423[281] = 0;
   out_3643040962092382423[282] = 0;
   out_3643040962092382423[283] = 0;
   out_3643040962092382423[284] = 0;
   out_3643040962092382423[285] = 1;
   out_3643040962092382423[286] = 0;
   out_3643040962092382423[287] = 0;
   out_3643040962092382423[288] = 0;
   out_3643040962092382423[289] = 0;
   out_3643040962092382423[290] = 0;
   out_3643040962092382423[291] = 0;
   out_3643040962092382423[292] = 0;
   out_3643040962092382423[293] = 0;
   out_3643040962092382423[294] = 0;
   out_3643040962092382423[295] = 0;
   out_3643040962092382423[296] = 0;
   out_3643040962092382423[297] = 0;
   out_3643040962092382423[298] = 0;
   out_3643040962092382423[299] = 0;
   out_3643040962092382423[300] = 0;
   out_3643040962092382423[301] = 0;
   out_3643040962092382423[302] = 0;
   out_3643040962092382423[303] = 0;
   out_3643040962092382423[304] = 1;
   out_3643040962092382423[305] = 0;
   out_3643040962092382423[306] = 0;
   out_3643040962092382423[307] = 0;
   out_3643040962092382423[308] = 0;
   out_3643040962092382423[309] = 0;
   out_3643040962092382423[310] = 0;
   out_3643040962092382423[311] = 0;
   out_3643040962092382423[312] = 0;
   out_3643040962092382423[313] = 0;
   out_3643040962092382423[314] = 0;
   out_3643040962092382423[315] = 0;
   out_3643040962092382423[316] = 0;
   out_3643040962092382423[317] = 0;
   out_3643040962092382423[318] = 0;
   out_3643040962092382423[319] = 0;
   out_3643040962092382423[320] = 0;
   out_3643040962092382423[321] = 0;
   out_3643040962092382423[322] = 0;
   out_3643040962092382423[323] = 1;
}
void h_4(double *state, double *unused, double *out_8854338774183858135) {
   out_8854338774183858135[0] = state[6] + state[9];
   out_8854338774183858135[1] = state[7] + state[10];
   out_8854338774183858135[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_8529830693005134694) {
   out_8529830693005134694[0] = 0;
   out_8529830693005134694[1] = 0;
   out_8529830693005134694[2] = 0;
   out_8529830693005134694[3] = 0;
   out_8529830693005134694[4] = 0;
   out_8529830693005134694[5] = 0;
   out_8529830693005134694[6] = 1;
   out_8529830693005134694[7] = 0;
   out_8529830693005134694[8] = 0;
   out_8529830693005134694[9] = 1;
   out_8529830693005134694[10] = 0;
   out_8529830693005134694[11] = 0;
   out_8529830693005134694[12] = 0;
   out_8529830693005134694[13] = 0;
   out_8529830693005134694[14] = 0;
   out_8529830693005134694[15] = 0;
   out_8529830693005134694[16] = 0;
   out_8529830693005134694[17] = 0;
   out_8529830693005134694[18] = 0;
   out_8529830693005134694[19] = 0;
   out_8529830693005134694[20] = 0;
   out_8529830693005134694[21] = 0;
   out_8529830693005134694[22] = 0;
   out_8529830693005134694[23] = 0;
   out_8529830693005134694[24] = 0;
   out_8529830693005134694[25] = 1;
   out_8529830693005134694[26] = 0;
   out_8529830693005134694[27] = 0;
   out_8529830693005134694[28] = 1;
   out_8529830693005134694[29] = 0;
   out_8529830693005134694[30] = 0;
   out_8529830693005134694[31] = 0;
   out_8529830693005134694[32] = 0;
   out_8529830693005134694[33] = 0;
   out_8529830693005134694[34] = 0;
   out_8529830693005134694[35] = 0;
   out_8529830693005134694[36] = 0;
   out_8529830693005134694[37] = 0;
   out_8529830693005134694[38] = 0;
   out_8529830693005134694[39] = 0;
   out_8529830693005134694[40] = 0;
   out_8529830693005134694[41] = 0;
   out_8529830693005134694[42] = 0;
   out_8529830693005134694[43] = 0;
   out_8529830693005134694[44] = 1;
   out_8529830693005134694[45] = 0;
   out_8529830693005134694[46] = 0;
   out_8529830693005134694[47] = 1;
   out_8529830693005134694[48] = 0;
   out_8529830693005134694[49] = 0;
   out_8529830693005134694[50] = 0;
   out_8529830693005134694[51] = 0;
   out_8529830693005134694[52] = 0;
   out_8529830693005134694[53] = 0;
}
void h_10(double *state, double *unused, double *out_5059906078839414114) {
   out_5059906078839414114[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_5059906078839414114[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_5059906078839414114[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_3583999604245367895) {
   out_3583999604245367895[0] = 0;
   out_3583999604245367895[1] = 9.8100000000000005*cos(state[1]);
   out_3583999604245367895[2] = 0;
   out_3583999604245367895[3] = 0;
   out_3583999604245367895[4] = -state[8];
   out_3583999604245367895[5] = state[7];
   out_3583999604245367895[6] = 0;
   out_3583999604245367895[7] = state[5];
   out_3583999604245367895[8] = -state[4];
   out_3583999604245367895[9] = 0;
   out_3583999604245367895[10] = 0;
   out_3583999604245367895[11] = 0;
   out_3583999604245367895[12] = 1;
   out_3583999604245367895[13] = 0;
   out_3583999604245367895[14] = 0;
   out_3583999604245367895[15] = 1;
   out_3583999604245367895[16] = 0;
   out_3583999604245367895[17] = 0;
   out_3583999604245367895[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_3583999604245367895[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_3583999604245367895[20] = 0;
   out_3583999604245367895[21] = state[8];
   out_3583999604245367895[22] = 0;
   out_3583999604245367895[23] = -state[6];
   out_3583999604245367895[24] = -state[5];
   out_3583999604245367895[25] = 0;
   out_3583999604245367895[26] = state[3];
   out_3583999604245367895[27] = 0;
   out_3583999604245367895[28] = 0;
   out_3583999604245367895[29] = 0;
   out_3583999604245367895[30] = 0;
   out_3583999604245367895[31] = 1;
   out_3583999604245367895[32] = 0;
   out_3583999604245367895[33] = 0;
   out_3583999604245367895[34] = 1;
   out_3583999604245367895[35] = 0;
   out_3583999604245367895[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_3583999604245367895[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_3583999604245367895[38] = 0;
   out_3583999604245367895[39] = -state[7];
   out_3583999604245367895[40] = state[6];
   out_3583999604245367895[41] = 0;
   out_3583999604245367895[42] = state[4];
   out_3583999604245367895[43] = -state[3];
   out_3583999604245367895[44] = 0;
   out_3583999604245367895[45] = 0;
   out_3583999604245367895[46] = 0;
   out_3583999604245367895[47] = 0;
   out_3583999604245367895[48] = 0;
   out_3583999604245367895[49] = 0;
   out_3583999604245367895[50] = 1;
   out_3583999604245367895[51] = 0;
   out_3583999604245367895[52] = 0;
   out_3583999604245367895[53] = 1;
}
void h_13(double *state, double *unused, double *out_7263365611470923251) {
   out_7263365611470923251[0] = state[3];
   out_7263365611470923251[1] = state[4];
   out_7263365611470923251[2] = state[5];
}
void H_13(double *state, double *unused, double *out_6704639555372084121) {
   out_6704639555372084121[0] = 0;
   out_6704639555372084121[1] = 0;
   out_6704639555372084121[2] = 0;
   out_6704639555372084121[3] = 1;
   out_6704639555372084121[4] = 0;
   out_6704639555372084121[5] = 0;
   out_6704639555372084121[6] = 0;
   out_6704639555372084121[7] = 0;
   out_6704639555372084121[8] = 0;
   out_6704639555372084121[9] = 0;
   out_6704639555372084121[10] = 0;
   out_6704639555372084121[11] = 0;
   out_6704639555372084121[12] = 0;
   out_6704639555372084121[13] = 0;
   out_6704639555372084121[14] = 0;
   out_6704639555372084121[15] = 0;
   out_6704639555372084121[16] = 0;
   out_6704639555372084121[17] = 0;
   out_6704639555372084121[18] = 0;
   out_6704639555372084121[19] = 0;
   out_6704639555372084121[20] = 0;
   out_6704639555372084121[21] = 0;
   out_6704639555372084121[22] = 1;
   out_6704639555372084121[23] = 0;
   out_6704639555372084121[24] = 0;
   out_6704639555372084121[25] = 0;
   out_6704639555372084121[26] = 0;
   out_6704639555372084121[27] = 0;
   out_6704639555372084121[28] = 0;
   out_6704639555372084121[29] = 0;
   out_6704639555372084121[30] = 0;
   out_6704639555372084121[31] = 0;
   out_6704639555372084121[32] = 0;
   out_6704639555372084121[33] = 0;
   out_6704639555372084121[34] = 0;
   out_6704639555372084121[35] = 0;
   out_6704639555372084121[36] = 0;
   out_6704639555372084121[37] = 0;
   out_6704639555372084121[38] = 0;
   out_6704639555372084121[39] = 0;
   out_6704639555372084121[40] = 0;
   out_6704639555372084121[41] = 1;
   out_6704639555372084121[42] = 0;
   out_6704639555372084121[43] = 0;
   out_6704639555372084121[44] = 0;
   out_6704639555372084121[45] = 0;
   out_6704639555372084121[46] = 0;
   out_6704639555372084121[47] = 0;
   out_6704639555372084121[48] = 0;
   out_6704639555372084121[49] = 0;
   out_6704639555372084121[50] = 0;
   out_6704639555372084121[51] = 0;
   out_6704639555372084121[52] = 0;
   out_6704639555372084121[53] = 0;
}
void h_14(double *state, double *unused, double *out_7190737918139558978) {
   out_7190737918139558978[0] = state[6];
   out_7190737918139558978[1] = state[7];
   out_7190737918139558978[2] = state[8];
}
void H_14(double *state, double *unused, double *out_5953672524364932393) {
   out_5953672524364932393[0] = 0;
   out_5953672524364932393[1] = 0;
   out_5953672524364932393[2] = 0;
   out_5953672524364932393[3] = 0;
   out_5953672524364932393[4] = 0;
   out_5953672524364932393[5] = 0;
   out_5953672524364932393[6] = 1;
   out_5953672524364932393[7] = 0;
   out_5953672524364932393[8] = 0;
   out_5953672524364932393[9] = 0;
   out_5953672524364932393[10] = 0;
   out_5953672524364932393[11] = 0;
   out_5953672524364932393[12] = 0;
   out_5953672524364932393[13] = 0;
   out_5953672524364932393[14] = 0;
   out_5953672524364932393[15] = 0;
   out_5953672524364932393[16] = 0;
   out_5953672524364932393[17] = 0;
   out_5953672524364932393[18] = 0;
   out_5953672524364932393[19] = 0;
   out_5953672524364932393[20] = 0;
   out_5953672524364932393[21] = 0;
   out_5953672524364932393[22] = 0;
   out_5953672524364932393[23] = 0;
   out_5953672524364932393[24] = 0;
   out_5953672524364932393[25] = 1;
   out_5953672524364932393[26] = 0;
   out_5953672524364932393[27] = 0;
   out_5953672524364932393[28] = 0;
   out_5953672524364932393[29] = 0;
   out_5953672524364932393[30] = 0;
   out_5953672524364932393[31] = 0;
   out_5953672524364932393[32] = 0;
   out_5953672524364932393[33] = 0;
   out_5953672524364932393[34] = 0;
   out_5953672524364932393[35] = 0;
   out_5953672524364932393[36] = 0;
   out_5953672524364932393[37] = 0;
   out_5953672524364932393[38] = 0;
   out_5953672524364932393[39] = 0;
   out_5953672524364932393[40] = 0;
   out_5953672524364932393[41] = 0;
   out_5953672524364932393[42] = 0;
   out_5953672524364932393[43] = 0;
   out_5953672524364932393[44] = 1;
   out_5953672524364932393[45] = 0;
   out_5953672524364932393[46] = 0;
   out_5953672524364932393[47] = 0;
   out_5953672524364932393[48] = 0;
   out_5953672524364932393[49] = 0;
   out_5953672524364932393[50] = 0;
   out_5953672524364932393[51] = 0;
   out_5953672524364932393[52] = 0;
   out_5953672524364932393[53] = 0;
}
#include <eigen3/Eigen/Dense>
#include <iostream>

typedef Eigen::Matrix<double, DIM, DIM, Eigen::RowMajor> DDM;
typedef Eigen::Matrix<double, EDIM, EDIM, Eigen::RowMajor> EEM;
typedef Eigen::Matrix<double, DIM, EDIM, Eigen::RowMajor> DEM;

void predict(double *in_x, double *in_P, double *in_Q, double dt) {
  typedef Eigen::Matrix<double, MEDIM, MEDIM, Eigen::RowMajor> RRM;

  double nx[DIM] = {0};
  double in_F[EDIM*EDIM] = {0};

  // functions from sympy
  f_fun(in_x, dt, nx);
  F_fun(in_x, dt, in_F);


  EEM F(in_F);
  EEM P(in_P);
  EEM Q(in_Q);

  RRM F_main = F.topLeftCorner(MEDIM, MEDIM);
  P.topLeftCorner(MEDIM, MEDIM) = (F_main * P.topLeftCorner(MEDIM, MEDIM)) * F_main.transpose();
  P.topRightCorner(MEDIM, EDIM - MEDIM) = F_main * P.topRightCorner(MEDIM, EDIM - MEDIM);
  P.bottomLeftCorner(EDIM - MEDIM, MEDIM) = P.bottomLeftCorner(EDIM - MEDIM, MEDIM) * F_main.transpose();

  P = P + dt*Q;

  // copy out state
  memcpy(in_x, nx, DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
}

// note: extra_args dim only correct when null space projecting
// otherwise 1
template <int ZDIM, int EADIM, bool MAHA_TEST>
void update(double *in_x, double *in_P, Hfun h_fun, Hfun H_fun, Hfun Hea_fun, double *in_z, double *in_R, double *in_ea, double MAHA_THRESHOLD) {
  typedef Eigen::Matrix<double, ZDIM, ZDIM, Eigen::RowMajor> ZZM;
  typedef Eigen::Matrix<double, ZDIM, DIM, Eigen::RowMajor> ZDM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, EDIM, Eigen::RowMajor> XEM;
  //typedef Eigen::Matrix<double, EDIM, ZDIM, Eigen::RowMajor> EZM;
  typedef Eigen::Matrix<double, Eigen::Dynamic, 1> X1M;
  typedef Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> XXM;

  double in_hx[ZDIM] = {0};
  double in_H[ZDIM * DIM] = {0};
  double in_H_mod[EDIM * DIM] = {0};
  double delta_x[EDIM] = {0};
  double x_new[DIM] = {0};


  // state x, P
  Eigen::Matrix<double, ZDIM, 1> z(in_z);
  EEM P(in_P);
  ZZM pre_R(in_R);

  // functions from sympy
  h_fun(in_x, in_ea, in_hx);
  H_fun(in_x, in_ea, in_H);
  ZDM pre_H(in_H);

  // get y (y = z - hx)
  Eigen::Matrix<double, ZDIM, 1> pre_y(in_hx); pre_y = z - pre_y;
  X1M y; XXM H; XXM R;
  if (Hea_fun){
    typedef Eigen::Matrix<double, ZDIM, EADIM, Eigen::RowMajor> ZAM;
    double in_Hea[ZDIM * EADIM] = {0};
    Hea_fun(in_x, in_ea, in_Hea);
    ZAM Hea(in_Hea);
    XXM A = Hea.transpose().fullPivLu().kernel();


    y = A.transpose() * pre_y;
    H = A.transpose() * pre_H;
    R = A.transpose() * pre_R * A;
  } else {
    y = pre_y;
    H = pre_H;
    R = pre_R;
  }
  // get modified H
  H_mod_fun(in_x, in_H_mod);
  DEM H_mod(in_H_mod);
  XEM H_err = H * H_mod;

  // Do mahalobis distance test
  if (MAHA_TEST){
    XXM a = (H_err * P * H_err.transpose() + R).inverse();
    double maha_dist = y.transpose() * a * y;
    if (maha_dist > MAHA_THRESHOLD){
      R = 1.0e16 * R;
    }
  }

  // Outlier resilient weighting
  double weight = 1;//(1.5)/(1 + y.squaredNorm()/R.sum());

  // kalman gains and I_KH
  XXM S = ((H_err * P) * H_err.transpose()) + R/weight;
  XEM KT = S.fullPivLu().solve(H_err * P.transpose());
  //EZM K = KT.transpose(); TODO: WHY DOES THIS NOT COMPILE?
  //EZM K = S.fullPivLu().solve(H_err * P.transpose()).transpose();
  //std::cout << "Here is the matrix rot:\n" << K << std::endl;
  EEM I_KH = Eigen::Matrix<double, EDIM, EDIM>::Identity() - (KT.transpose() * H_err);

  // update state by injecting dx
  Eigen::Matrix<double, EDIM, 1> dx(delta_x);
  dx  = (KT.transpose() * y);
  memcpy(delta_x, dx.data(), EDIM * sizeof(double));
  err_fun(in_x, delta_x, x_new);
  Eigen::Matrix<double, DIM, 1> x(x_new);

  // update cov
  P = ((I_KH * P) * I_KH.transpose()) + ((KT.transpose() * R) * KT);

  // copy out state
  memcpy(in_x, x.data(), DIM * sizeof(double));
  memcpy(in_P, P.data(), EDIM * EDIM * sizeof(double));
  memcpy(in_z, y.data(), y.rows() * sizeof(double));
}




}
extern "C" {

void pose_update_4(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_4, H_4, NULL, in_z, in_R, in_ea, MAHA_THRESH_4);
}
void pose_update_10(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_10, H_10, NULL, in_z, in_R, in_ea, MAHA_THRESH_10);
}
void pose_update_13(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_13, H_13, NULL, in_z, in_R, in_ea, MAHA_THRESH_13);
}
void pose_update_14(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<3, 3, 0>(in_x, in_P, h_14, H_14, NULL, in_z, in_R, in_ea, MAHA_THRESH_14);
}
void pose_err_fun(double *nom_x, double *delta_x, double *out_671460305092226609) {
  err_fun(nom_x, delta_x, out_671460305092226609);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_8594657692984849886) {
  inv_err_fun(nom_x, true_x, out_8594657692984849886);
}
void pose_H_mod_fun(double *state, double *out_6213728924716372500) {
  H_mod_fun(state, out_6213728924716372500);
}
void pose_f_fun(double *state, double dt, double *out_5585784149500665013) {
  f_fun(state,  dt, out_5585784149500665013);
}
void pose_F_fun(double *state, double dt, double *out_3643040962092382423) {
  F_fun(state,  dt, out_3643040962092382423);
}
void pose_h_4(double *state, double *unused, double *out_8854338774183858135) {
  h_4(state, unused, out_8854338774183858135);
}
void pose_H_4(double *state, double *unused, double *out_8529830693005134694) {
  H_4(state, unused, out_8529830693005134694);
}
void pose_h_10(double *state, double *unused, double *out_5059906078839414114) {
  h_10(state, unused, out_5059906078839414114);
}
void pose_H_10(double *state, double *unused, double *out_3583999604245367895) {
  H_10(state, unused, out_3583999604245367895);
}
void pose_h_13(double *state, double *unused, double *out_7263365611470923251) {
  h_13(state, unused, out_7263365611470923251);
}
void pose_H_13(double *state, double *unused, double *out_6704639555372084121) {
  H_13(state, unused, out_6704639555372084121);
}
void pose_h_14(double *state, double *unused, double *out_7190737918139558978) {
  h_14(state, unused, out_7190737918139558978);
}
void pose_H_14(double *state, double *unused, double *out_5953672524364932393) {
  H_14(state, unused, out_5953672524364932393);
}
void pose_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
}

const EKF pose = {
  .name = "pose",
  .kinds = { 4, 10, 13, 14 },
  .feature_kinds = {  },
  .f_fun = pose_f_fun,
  .F_fun = pose_F_fun,
  .err_fun = pose_err_fun,
  .inv_err_fun = pose_inv_err_fun,
  .H_mod_fun = pose_H_mod_fun,
  .predict = pose_predict,
  .hs = {
    { 4, pose_h_4 },
    { 10, pose_h_10 },
    { 13, pose_h_13 },
    { 14, pose_h_14 },
  },
  .Hs = {
    { 4, pose_H_4 },
    { 10, pose_H_10 },
    { 13, pose_H_13 },
    { 14, pose_H_14 },
  },
  .updates = {
    { 4, pose_update_4 },
    { 10, pose_update_10 },
    { 13, pose_update_13 },
    { 14, pose_update_14 },
  },
  .Hes = {
  },
  .sets = {
  },
  .extra_routines = {
  },
};

ekf_lib_init(pose)
