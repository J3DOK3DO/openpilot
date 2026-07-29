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
void err_fun(double *nom_x, double *delta_x, double *out_7616755969345465164) {
   out_7616755969345465164[0] = delta_x[0] + nom_x[0];
   out_7616755969345465164[1] = delta_x[1] + nom_x[1];
   out_7616755969345465164[2] = delta_x[2] + nom_x[2];
   out_7616755969345465164[3] = delta_x[3] + nom_x[3];
   out_7616755969345465164[4] = delta_x[4] + nom_x[4];
   out_7616755969345465164[5] = delta_x[5] + nom_x[5];
   out_7616755969345465164[6] = delta_x[6] + nom_x[6];
   out_7616755969345465164[7] = delta_x[7] + nom_x[7];
   out_7616755969345465164[8] = delta_x[8] + nom_x[8];
   out_7616755969345465164[9] = delta_x[9] + nom_x[9];
   out_7616755969345465164[10] = delta_x[10] + nom_x[10];
   out_7616755969345465164[11] = delta_x[11] + nom_x[11];
   out_7616755969345465164[12] = delta_x[12] + nom_x[12];
   out_7616755969345465164[13] = delta_x[13] + nom_x[13];
   out_7616755969345465164[14] = delta_x[14] + nom_x[14];
   out_7616755969345465164[15] = delta_x[15] + nom_x[15];
   out_7616755969345465164[16] = delta_x[16] + nom_x[16];
   out_7616755969345465164[17] = delta_x[17] + nom_x[17];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_2983579217144166569) {
   out_2983579217144166569[0] = -nom_x[0] + true_x[0];
   out_2983579217144166569[1] = -nom_x[1] + true_x[1];
   out_2983579217144166569[2] = -nom_x[2] + true_x[2];
   out_2983579217144166569[3] = -nom_x[3] + true_x[3];
   out_2983579217144166569[4] = -nom_x[4] + true_x[4];
   out_2983579217144166569[5] = -nom_x[5] + true_x[5];
   out_2983579217144166569[6] = -nom_x[6] + true_x[6];
   out_2983579217144166569[7] = -nom_x[7] + true_x[7];
   out_2983579217144166569[8] = -nom_x[8] + true_x[8];
   out_2983579217144166569[9] = -nom_x[9] + true_x[9];
   out_2983579217144166569[10] = -nom_x[10] + true_x[10];
   out_2983579217144166569[11] = -nom_x[11] + true_x[11];
   out_2983579217144166569[12] = -nom_x[12] + true_x[12];
   out_2983579217144166569[13] = -nom_x[13] + true_x[13];
   out_2983579217144166569[14] = -nom_x[14] + true_x[14];
   out_2983579217144166569[15] = -nom_x[15] + true_x[15];
   out_2983579217144166569[16] = -nom_x[16] + true_x[16];
   out_2983579217144166569[17] = -nom_x[17] + true_x[17];
}
void H_mod_fun(double *state, double *out_7561037298851331177) {
   out_7561037298851331177[0] = 1.0;
   out_7561037298851331177[1] = 0.0;
   out_7561037298851331177[2] = 0.0;
   out_7561037298851331177[3] = 0.0;
   out_7561037298851331177[4] = 0.0;
   out_7561037298851331177[5] = 0.0;
   out_7561037298851331177[6] = 0.0;
   out_7561037298851331177[7] = 0.0;
   out_7561037298851331177[8] = 0.0;
   out_7561037298851331177[9] = 0.0;
   out_7561037298851331177[10] = 0.0;
   out_7561037298851331177[11] = 0.0;
   out_7561037298851331177[12] = 0.0;
   out_7561037298851331177[13] = 0.0;
   out_7561037298851331177[14] = 0.0;
   out_7561037298851331177[15] = 0.0;
   out_7561037298851331177[16] = 0.0;
   out_7561037298851331177[17] = 0.0;
   out_7561037298851331177[18] = 0.0;
   out_7561037298851331177[19] = 1.0;
   out_7561037298851331177[20] = 0.0;
   out_7561037298851331177[21] = 0.0;
   out_7561037298851331177[22] = 0.0;
   out_7561037298851331177[23] = 0.0;
   out_7561037298851331177[24] = 0.0;
   out_7561037298851331177[25] = 0.0;
   out_7561037298851331177[26] = 0.0;
   out_7561037298851331177[27] = 0.0;
   out_7561037298851331177[28] = 0.0;
   out_7561037298851331177[29] = 0.0;
   out_7561037298851331177[30] = 0.0;
   out_7561037298851331177[31] = 0.0;
   out_7561037298851331177[32] = 0.0;
   out_7561037298851331177[33] = 0.0;
   out_7561037298851331177[34] = 0.0;
   out_7561037298851331177[35] = 0.0;
   out_7561037298851331177[36] = 0.0;
   out_7561037298851331177[37] = 0.0;
   out_7561037298851331177[38] = 1.0;
   out_7561037298851331177[39] = 0.0;
   out_7561037298851331177[40] = 0.0;
   out_7561037298851331177[41] = 0.0;
   out_7561037298851331177[42] = 0.0;
   out_7561037298851331177[43] = 0.0;
   out_7561037298851331177[44] = 0.0;
   out_7561037298851331177[45] = 0.0;
   out_7561037298851331177[46] = 0.0;
   out_7561037298851331177[47] = 0.0;
   out_7561037298851331177[48] = 0.0;
   out_7561037298851331177[49] = 0.0;
   out_7561037298851331177[50] = 0.0;
   out_7561037298851331177[51] = 0.0;
   out_7561037298851331177[52] = 0.0;
   out_7561037298851331177[53] = 0.0;
   out_7561037298851331177[54] = 0.0;
   out_7561037298851331177[55] = 0.0;
   out_7561037298851331177[56] = 0.0;
   out_7561037298851331177[57] = 1.0;
   out_7561037298851331177[58] = 0.0;
   out_7561037298851331177[59] = 0.0;
   out_7561037298851331177[60] = 0.0;
   out_7561037298851331177[61] = 0.0;
   out_7561037298851331177[62] = 0.0;
   out_7561037298851331177[63] = 0.0;
   out_7561037298851331177[64] = 0.0;
   out_7561037298851331177[65] = 0.0;
   out_7561037298851331177[66] = 0.0;
   out_7561037298851331177[67] = 0.0;
   out_7561037298851331177[68] = 0.0;
   out_7561037298851331177[69] = 0.0;
   out_7561037298851331177[70] = 0.0;
   out_7561037298851331177[71] = 0.0;
   out_7561037298851331177[72] = 0.0;
   out_7561037298851331177[73] = 0.0;
   out_7561037298851331177[74] = 0.0;
   out_7561037298851331177[75] = 0.0;
   out_7561037298851331177[76] = 1.0;
   out_7561037298851331177[77] = 0.0;
   out_7561037298851331177[78] = 0.0;
   out_7561037298851331177[79] = 0.0;
   out_7561037298851331177[80] = 0.0;
   out_7561037298851331177[81] = 0.0;
   out_7561037298851331177[82] = 0.0;
   out_7561037298851331177[83] = 0.0;
   out_7561037298851331177[84] = 0.0;
   out_7561037298851331177[85] = 0.0;
   out_7561037298851331177[86] = 0.0;
   out_7561037298851331177[87] = 0.0;
   out_7561037298851331177[88] = 0.0;
   out_7561037298851331177[89] = 0.0;
   out_7561037298851331177[90] = 0.0;
   out_7561037298851331177[91] = 0.0;
   out_7561037298851331177[92] = 0.0;
   out_7561037298851331177[93] = 0.0;
   out_7561037298851331177[94] = 0.0;
   out_7561037298851331177[95] = 1.0;
   out_7561037298851331177[96] = 0.0;
   out_7561037298851331177[97] = 0.0;
   out_7561037298851331177[98] = 0.0;
   out_7561037298851331177[99] = 0.0;
   out_7561037298851331177[100] = 0.0;
   out_7561037298851331177[101] = 0.0;
   out_7561037298851331177[102] = 0.0;
   out_7561037298851331177[103] = 0.0;
   out_7561037298851331177[104] = 0.0;
   out_7561037298851331177[105] = 0.0;
   out_7561037298851331177[106] = 0.0;
   out_7561037298851331177[107] = 0.0;
   out_7561037298851331177[108] = 0.0;
   out_7561037298851331177[109] = 0.0;
   out_7561037298851331177[110] = 0.0;
   out_7561037298851331177[111] = 0.0;
   out_7561037298851331177[112] = 0.0;
   out_7561037298851331177[113] = 0.0;
   out_7561037298851331177[114] = 1.0;
   out_7561037298851331177[115] = 0.0;
   out_7561037298851331177[116] = 0.0;
   out_7561037298851331177[117] = 0.0;
   out_7561037298851331177[118] = 0.0;
   out_7561037298851331177[119] = 0.0;
   out_7561037298851331177[120] = 0.0;
   out_7561037298851331177[121] = 0.0;
   out_7561037298851331177[122] = 0.0;
   out_7561037298851331177[123] = 0.0;
   out_7561037298851331177[124] = 0.0;
   out_7561037298851331177[125] = 0.0;
   out_7561037298851331177[126] = 0.0;
   out_7561037298851331177[127] = 0.0;
   out_7561037298851331177[128] = 0.0;
   out_7561037298851331177[129] = 0.0;
   out_7561037298851331177[130] = 0.0;
   out_7561037298851331177[131] = 0.0;
   out_7561037298851331177[132] = 0.0;
   out_7561037298851331177[133] = 1.0;
   out_7561037298851331177[134] = 0.0;
   out_7561037298851331177[135] = 0.0;
   out_7561037298851331177[136] = 0.0;
   out_7561037298851331177[137] = 0.0;
   out_7561037298851331177[138] = 0.0;
   out_7561037298851331177[139] = 0.0;
   out_7561037298851331177[140] = 0.0;
   out_7561037298851331177[141] = 0.0;
   out_7561037298851331177[142] = 0.0;
   out_7561037298851331177[143] = 0.0;
   out_7561037298851331177[144] = 0.0;
   out_7561037298851331177[145] = 0.0;
   out_7561037298851331177[146] = 0.0;
   out_7561037298851331177[147] = 0.0;
   out_7561037298851331177[148] = 0.0;
   out_7561037298851331177[149] = 0.0;
   out_7561037298851331177[150] = 0.0;
   out_7561037298851331177[151] = 0.0;
   out_7561037298851331177[152] = 1.0;
   out_7561037298851331177[153] = 0.0;
   out_7561037298851331177[154] = 0.0;
   out_7561037298851331177[155] = 0.0;
   out_7561037298851331177[156] = 0.0;
   out_7561037298851331177[157] = 0.0;
   out_7561037298851331177[158] = 0.0;
   out_7561037298851331177[159] = 0.0;
   out_7561037298851331177[160] = 0.0;
   out_7561037298851331177[161] = 0.0;
   out_7561037298851331177[162] = 0.0;
   out_7561037298851331177[163] = 0.0;
   out_7561037298851331177[164] = 0.0;
   out_7561037298851331177[165] = 0.0;
   out_7561037298851331177[166] = 0.0;
   out_7561037298851331177[167] = 0.0;
   out_7561037298851331177[168] = 0.0;
   out_7561037298851331177[169] = 0.0;
   out_7561037298851331177[170] = 0.0;
   out_7561037298851331177[171] = 1.0;
   out_7561037298851331177[172] = 0.0;
   out_7561037298851331177[173] = 0.0;
   out_7561037298851331177[174] = 0.0;
   out_7561037298851331177[175] = 0.0;
   out_7561037298851331177[176] = 0.0;
   out_7561037298851331177[177] = 0.0;
   out_7561037298851331177[178] = 0.0;
   out_7561037298851331177[179] = 0.0;
   out_7561037298851331177[180] = 0.0;
   out_7561037298851331177[181] = 0.0;
   out_7561037298851331177[182] = 0.0;
   out_7561037298851331177[183] = 0.0;
   out_7561037298851331177[184] = 0.0;
   out_7561037298851331177[185] = 0.0;
   out_7561037298851331177[186] = 0.0;
   out_7561037298851331177[187] = 0.0;
   out_7561037298851331177[188] = 0.0;
   out_7561037298851331177[189] = 0.0;
   out_7561037298851331177[190] = 1.0;
   out_7561037298851331177[191] = 0.0;
   out_7561037298851331177[192] = 0.0;
   out_7561037298851331177[193] = 0.0;
   out_7561037298851331177[194] = 0.0;
   out_7561037298851331177[195] = 0.0;
   out_7561037298851331177[196] = 0.0;
   out_7561037298851331177[197] = 0.0;
   out_7561037298851331177[198] = 0.0;
   out_7561037298851331177[199] = 0.0;
   out_7561037298851331177[200] = 0.0;
   out_7561037298851331177[201] = 0.0;
   out_7561037298851331177[202] = 0.0;
   out_7561037298851331177[203] = 0.0;
   out_7561037298851331177[204] = 0.0;
   out_7561037298851331177[205] = 0.0;
   out_7561037298851331177[206] = 0.0;
   out_7561037298851331177[207] = 0.0;
   out_7561037298851331177[208] = 0.0;
   out_7561037298851331177[209] = 1.0;
   out_7561037298851331177[210] = 0.0;
   out_7561037298851331177[211] = 0.0;
   out_7561037298851331177[212] = 0.0;
   out_7561037298851331177[213] = 0.0;
   out_7561037298851331177[214] = 0.0;
   out_7561037298851331177[215] = 0.0;
   out_7561037298851331177[216] = 0.0;
   out_7561037298851331177[217] = 0.0;
   out_7561037298851331177[218] = 0.0;
   out_7561037298851331177[219] = 0.0;
   out_7561037298851331177[220] = 0.0;
   out_7561037298851331177[221] = 0.0;
   out_7561037298851331177[222] = 0.0;
   out_7561037298851331177[223] = 0.0;
   out_7561037298851331177[224] = 0.0;
   out_7561037298851331177[225] = 0.0;
   out_7561037298851331177[226] = 0.0;
   out_7561037298851331177[227] = 0.0;
   out_7561037298851331177[228] = 1.0;
   out_7561037298851331177[229] = 0.0;
   out_7561037298851331177[230] = 0.0;
   out_7561037298851331177[231] = 0.0;
   out_7561037298851331177[232] = 0.0;
   out_7561037298851331177[233] = 0.0;
   out_7561037298851331177[234] = 0.0;
   out_7561037298851331177[235] = 0.0;
   out_7561037298851331177[236] = 0.0;
   out_7561037298851331177[237] = 0.0;
   out_7561037298851331177[238] = 0.0;
   out_7561037298851331177[239] = 0.0;
   out_7561037298851331177[240] = 0.0;
   out_7561037298851331177[241] = 0.0;
   out_7561037298851331177[242] = 0.0;
   out_7561037298851331177[243] = 0.0;
   out_7561037298851331177[244] = 0.0;
   out_7561037298851331177[245] = 0.0;
   out_7561037298851331177[246] = 0.0;
   out_7561037298851331177[247] = 1.0;
   out_7561037298851331177[248] = 0.0;
   out_7561037298851331177[249] = 0.0;
   out_7561037298851331177[250] = 0.0;
   out_7561037298851331177[251] = 0.0;
   out_7561037298851331177[252] = 0.0;
   out_7561037298851331177[253] = 0.0;
   out_7561037298851331177[254] = 0.0;
   out_7561037298851331177[255] = 0.0;
   out_7561037298851331177[256] = 0.0;
   out_7561037298851331177[257] = 0.0;
   out_7561037298851331177[258] = 0.0;
   out_7561037298851331177[259] = 0.0;
   out_7561037298851331177[260] = 0.0;
   out_7561037298851331177[261] = 0.0;
   out_7561037298851331177[262] = 0.0;
   out_7561037298851331177[263] = 0.0;
   out_7561037298851331177[264] = 0.0;
   out_7561037298851331177[265] = 0.0;
   out_7561037298851331177[266] = 1.0;
   out_7561037298851331177[267] = 0.0;
   out_7561037298851331177[268] = 0.0;
   out_7561037298851331177[269] = 0.0;
   out_7561037298851331177[270] = 0.0;
   out_7561037298851331177[271] = 0.0;
   out_7561037298851331177[272] = 0.0;
   out_7561037298851331177[273] = 0.0;
   out_7561037298851331177[274] = 0.0;
   out_7561037298851331177[275] = 0.0;
   out_7561037298851331177[276] = 0.0;
   out_7561037298851331177[277] = 0.0;
   out_7561037298851331177[278] = 0.0;
   out_7561037298851331177[279] = 0.0;
   out_7561037298851331177[280] = 0.0;
   out_7561037298851331177[281] = 0.0;
   out_7561037298851331177[282] = 0.0;
   out_7561037298851331177[283] = 0.0;
   out_7561037298851331177[284] = 0.0;
   out_7561037298851331177[285] = 1.0;
   out_7561037298851331177[286] = 0.0;
   out_7561037298851331177[287] = 0.0;
   out_7561037298851331177[288] = 0.0;
   out_7561037298851331177[289] = 0.0;
   out_7561037298851331177[290] = 0.0;
   out_7561037298851331177[291] = 0.0;
   out_7561037298851331177[292] = 0.0;
   out_7561037298851331177[293] = 0.0;
   out_7561037298851331177[294] = 0.0;
   out_7561037298851331177[295] = 0.0;
   out_7561037298851331177[296] = 0.0;
   out_7561037298851331177[297] = 0.0;
   out_7561037298851331177[298] = 0.0;
   out_7561037298851331177[299] = 0.0;
   out_7561037298851331177[300] = 0.0;
   out_7561037298851331177[301] = 0.0;
   out_7561037298851331177[302] = 0.0;
   out_7561037298851331177[303] = 0.0;
   out_7561037298851331177[304] = 1.0;
   out_7561037298851331177[305] = 0.0;
   out_7561037298851331177[306] = 0.0;
   out_7561037298851331177[307] = 0.0;
   out_7561037298851331177[308] = 0.0;
   out_7561037298851331177[309] = 0.0;
   out_7561037298851331177[310] = 0.0;
   out_7561037298851331177[311] = 0.0;
   out_7561037298851331177[312] = 0.0;
   out_7561037298851331177[313] = 0.0;
   out_7561037298851331177[314] = 0.0;
   out_7561037298851331177[315] = 0.0;
   out_7561037298851331177[316] = 0.0;
   out_7561037298851331177[317] = 0.0;
   out_7561037298851331177[318] = 0.0;
   out_7561037298851331177[319] = 0.0;
   out_7561037298851331177[320] = 0.0;
   out_7561037298851331177[321] = 0.0;
   out_7561037298851331177[322] = 0.0;
   out_7561037298851331177[323] = 1.0;
}
void f_fun(double *state, double dt, double *out_5713485962747764656) {
   out_5713485962747764656[0] = atan2((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), -(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]));
   out_5713485962747764656[1] = asin(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]));
   out_5713485962747764656[2] = atan2(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), -(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]));
   out_5713485962747764656[3] = dt*state[12] + state[3];
   out_5713485962747764656[4] = dt*state[13] + state[4];
   out_5713485962747764656[5] = dt*state[14] + state[5];
   out_5713485962747764656[6] = state[6];
   out_5713485962747764656[7] = state[7];
   out_5713485962747764656[8] = state[8];
   out_5713485962747764656[9] = state[9];
   out_5713485962747764656[10] = state[10];
   out_5713485962747764656[11] = state[11];
   out_5713485962747764656[12] = state[12];
   out_5713485962747764656[13] = state[13];
   out_5713485962747764656[14] = state[14];
   out_5713485962747764656[15] = state[15];
   out_5713485962747764656[16] = state[16];
   out_5713485962747764656[17] = state[17];
}
void F_fun(double *state, double dt, double *out_958271563642232375) {
   out_958271563642232375[0] = ((-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*cos(state[0])*cos(state[1]) - sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*cos(state[0])*cos(state[1]) - sin(dt*state[6])*sin(state[0])*cos(dt*state[7])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_958271563642232375[1] = ((-sin(dt*state[6])*sin(dt*state[8]) - sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*cos(state[1]) - (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*sin(state[1]) - sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(state[0]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*sin(state[1]) + (-sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) + sin(dt*state[8])*cos(dt*state[6]))*cos(state[1]) - sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(state[0]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_958271563642232375[2] = 0;
   out_958271563642232375[3] = 0;
   out_958271563642232375[4] = 0;
   out_958271563642232375[5] = 0;
   out_958271563642232375[6] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(dt*cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) - dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_958271563642232375[7] = (-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[6])*sin(dt*state[7])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[6])*sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) - dt*sin(dt*state[6])*sin(state[1])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + (-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))*(-dt*sin(dt*state[7])*cos(dt*state[6])*cos(state[0])*cos(state[1]) + dt*sin(dt*state[8])*sin(state[0])*cos(dt*state[6])*cos(dt*state[7])*cos(state[1]) - dt*sin(state[1])*cos(dt*state[6])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_958271563642232375[8] = ((dt*sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + dt*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (dt*sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]))*(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2)) + ((dt*sin(dt*state[6])*sin(dt*state[8]) + dt*sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (-dt*sin(dt*state[6])*cos(dt*state[8]) + dt*sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]))*(-(sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) + (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) - sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/(pow(-(sin(dt*state[6])*sin(dt*state[8]) + sin(dt*state[7])*cos(dt*state[6])*cos(dt*state[8]))*sin(state[1]) + (-sin(dt*state[6])*cos(dt*state[8]) + sin(dt*state[7])*sin(dt*state[8])*cos(dt*state[6]))*sin(state[0])*cos(state[1]) + cos(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2) + pow((sin(dt*state[6])*sin(dt*state[7])*sin(dt*state[8]) + cos(dt*state[6])*cos(dt*state[8]))*sin(state[0])*cos(state[1]) - (sin(dt*state[6])*sin(dt*state[7])*cos(dt*state[8]) - sin(dt*state[8])*cos(dt*state[6]))*sin(state[1]) + sin(dt*state[6])*cos(dt*state[7])*cos(state[0])*cos(state[1]), 2));
   out_958271563642232375[9] = 0;
   out_958271563642232375[10] = 0;
   out_958271563642232375[11] = 0;
   out_958271563642232375[12] = 0;
   out_958271563642232375[13] = 0;
   out_958271563642232375[14] = 0;
   out_958271563642232375[15] = 0;
   out_958271563642232375[16] = 0;
   out_958271563642232375[17] = 0;
   out_958271563642232375[18] = (-sin(dt*state[7])*sin(state[0])*cos(state[1]) - sin(dt*state[8])*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_958271563642232375[19] = (-sin(dt*state[7])*sin(state[1])*cos(state[0]) + sin(dt*state[8])*sin(state[0])*sin(state[1])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_958271563642232375[20] = 0;
   out_958271563642232375[21] = 0;
   out_958271563642232375[22] = 0;
   out_958271563642232375[23] = 0;
   out_958271563642232375[24] = 0;
   out_958271563642232375[25] = (dt*sin(dt*state[7])*sin(dt*state[8])*sin(state[0])*cos(state[1]) - dt*sin(dt*state[7])*sin(state[1])*cos(dt*state[8]) + dt*cos(dt*state[7])*cos(state[0])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_958271563642232375[26] = (-dt*sin(dt*state[8])*sin(state[1])*cos(dt*state[7]) - dt*sin(state[0])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/sqrt(1 - pow(sin(dt*state[7])*cos(state[0])*cos(state[1]) - sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1]) + sin(state[1])*cos(dt*state[7])*cos(dt*state[8]), 2));
   out_958271563642232375[27] = 0;
   out_958271563642232375[28] = 0;
   out_958271563642232375[29] = 0;
   out_958271563642232375[30] = 0;
   out_958271563642232375[31] = 0;
   out_958271563642232375[32] = 0;
   out_958271563642232375[33] = 0;
   out_958271563642232375[34] = 0;
   out_958271563642232375[35] = 0;
   out_958271563642232375[36] = ((sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_958271563642232375[37] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-sin(dt*state[7])*sin(state[2])*cos(state[0])*cos(state[1]) + sin(dt*state[8])*sin(state[0])*sin(state[2])*cos(dt*state[7])*cos(state[1]) - sin(state[1])*sin(state[2])*cos(dt*state[7])*cos(dt*state[8]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(-sin(dt*state[7])*cos(state[0])*cos(state[1])*cos(state[2]) + sin(dt*state[8])*sin(state[0])*cos(dt*state[7])*cos(state[1])*cos(state[2]) - sin(state[1])*cos(dt*state[7])*cos(dt*state[8])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_958271563642232375[38] = ((-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (-sin(state[0])*sin(state[1])*sin(state[2]) - cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_958271563642232375[39] = 0;
   out_958271563642232375[40] = 0;
   out_958271563642232375[41] = 0;
   out_958271563642232375[42] = 0;
   out_958271563642232375[43] = (-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))*(dt*(sin(state[0])*cos(state[2]) - sin(state[1])*sin(state[2])*cos(state[0]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*sin(state[2])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + ((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))*(dt*(-sin(state[0])*sin(state[2]) - sin(state[1])*cos(state[0])*cos(state[2]))*cos(dt*state[7]) - dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[7])*sin(dt*state[8]) - dt*sin(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_958271563642232375[44] = (dt*(sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*sin(state[2])*cos(dt*state[7])*cos(state[1]))*(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2)) + (dt*(sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*cos(dt*state[7])*cos(dt*state[8]) - dt*sin(dt*state[8])*cos(dt*state[7])*cos(state[1])*cos(state[2]))*((-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) - (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) - sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]))/(pow(-(sin(state[0])*sin(state[2]) + sin(state[1])*cos(state[0])*cos(state[2]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*cos(state[2]) - sin(state[2])*cos(state[0]))*sin(dt*state[8])*cos(dt*state[7]) + cos(dt*state[7])*cos(dt*state[8])*cos(state[1])*cos(state[2]), 2) + pow(-(-sin(state[0])*cos(state[2]) + sin(state[1])*sin(state[2])*cos(state[0]))*sin(dt*state[7]) + (sin(state[0])*sin(state[1])*sin(state[2]) + cos(state[0])*cos(state[2]))*sin(dt*state[8])*cos(dt*state[7]) + sin(state[2])*cos(dt*state[7])*cos(dt*state[8])*cos(state[1]), 2));
   out_958271563642232375[45] = 0;
   out_958271563642232375[46] = 0;
   out_958271563642232375[47] = 0;
   out_958271563642232375[48] = 0;
   out_958271563642232375[49] = 0;
   out_958271563642232375[50] = 0;
   out_958271563642232375[51] = 0;
   out_958271563642232375[52] = 0;
   out_958271563642232375[53] = 0;
   out_958271563642232375[54] = 0;
   out_958271563642232375[55] = 0;
   out_958271563642232375[56] = 0;
   out_958271563642232375[57] = 1;
   out_958271563642232375[58] = 0;
   out_958271563642232375[59] = 0;
   out_958271563642232375[60] = 0;
   out_958271563642232375[61] = 0;
   out_958271563642232375[62] = 0;
   out_958271563642232375[63] = 0;
   out_958271563642232375[64] = 0;
   out_958271563642232375[65] = 0;
   out_958271563642232375[66] = dt;
   out_958271563642232375[67] = 0;
   out_958271563642232375[68] = 0;
   out_958271563642232375[69] = 0;
   out_958271563642232375[70] = 0;
   out_958271563642232375[71] = 0;
   out_958271563642232375[72] = 0;
   out_958271563642232375[73] = 0;
   out_958271563642232375[74] = 0;
   out_958271563642232375[75] = 0;
   out_958271563642232375[76] = 1;
   out_958271563642232375[77] = 0;
   out_958271563642232375[78] = 0;
   out_958271563642232375[79] = 0;
   out_958271563642232375[80] = 0;
   out_958271563642232375[81] = 0;
   out_958271563642232375[82] = 0;
   out_958271563642232375[83] = 0;
   out_958271563642232375[84] = 0;
   out_958271563642232375[85] = dt;
   out_958271563642232375[86] = 0;
   out_958271563642232375[87] = 0;
   out_958271563642232375[88] = 0;
   out_958271563642232375[89] = 0;
   out_958271563642232375[90] = 0;
   out_958271563642232375[91] = 0;
   out_958271563642232375[92] = 0;
   out_958271563642232375[93] = 0;
   out_958271563642232375[94] = 0;
   out_958271563642232375[95] = 1;
   out_958271563642232375[96] = 0;
   out_958271563642232375[97] = 0;
   out_958271563642232375[98] = 0;
   out_958271563642232375[99] = 0;
   out_958271563642232375[100] = 0;
   out_958271563642232375[101] = 0;
   out_958271563642232375[102] = 0;
   out_958271563642232375[103] = 0;
   out_958271563642232375[104] = dt;
   out_958271563642232375[105] = 0;
   out_958271563642232375[106] = 0;
   out_958271563642232375[107] = 0;
   out_958271563642232375[108] = 0;
   out_958271563642232375[109] = 0;
   out_958271563642232375[110] = 0;
   out_958271563642232375[111] = 0;
   out_958271563642232375[112] = 0;
   out_958271563642232375[113] = 0;
   out_958271563642232375[114] = 1;
   out_958271563642232375[115] = 0;
   out_958271563642232375[116] = 0;
   out_958271563642232375[117] = 0;
   out_958271563642232375[118] = 0;
   out_958271563642232375[119] = 0;
   out_958271563642232375[120] = 0;
   out_958271563642232375[121] = 0;
   out_958271563642232375[122] = 0;
   out_958271563642232375[123] = 0;
   out_958271563642232375[124] = 0;
   out_958271563642232375[125] = 0;
   out_958271563642232375[126] = 0;
   out_958271563642232375[127] = 0;
   out_958271563642232375[128] = 0;
   out_958271563642232375[129] = 0;
   out_958271563642232375[130] = 0;
   out_958271563642232375[131] = 0;
   out_958271563642232375[132] = 0;
   out_958271563642232375[133] = 1;
   out_958271563642232375[134] = 0;
   out_958271563642232375[135] = 0;
   out_958271563642232375[136] = 0;
   out_958271563642232375[137] = 0;
   out_958271563642232375[138] = 0;
   out_958271563642232375[139] = 0;
   out_958271563642232375[140] = 0;
   out_958271563642232375[141] = 0;
   out_958271563642232375[142] = 0;
   out_958271563642232375[143] = 0;
   out_958271563642232375[144] = 0;
   out_958271563642232375[145] = 0;
   out_958271563642232375[146] = 0;
   out_958271563642232375[147] = 0;
   out_958271563642232375[148] = 0;
   out_958271563642232375[149] = 0;
   out_958271563642232375[150] = 0;
   out_958271563642232375[151] = 0;
   out_958271563642232375[152] = 1;
   out_958271563642232375[153] = 0;
   out_958271563642232375[154] = 0;
   out_958271563642232375[155] = 0;
   out_958271563642232375[156] = 0;
   out_958271563642232375[157] = 0;
   out_958271563642232375[158] = 0;
   out_958271563642232375[159] = 0;
   out_958271563642232375[160] = 0;
   out_958271563642232375[161] = 0;
   out_958271563642232375[162] = 0;
   out_958271563642232375[163] = 0;
   out_958271563642232375[164] = 0;
   out_958271563642232375[165] = 0;
   out_958271563642232375[166] = 0;
   out_958271563642232375[167] = 0;
   out_958271563642232375[168] = 0;
   out_958271563642232375[169] = 0;
   out_958271563642232375[170] = 0;
   out_958271563642232375[171] = 1;
   out_958271563642232375[172] = 0;
   out_958271563642232375[173] = 0;
   out_958271563642232375[174] = 0;
   out_958271563642232375[175] = 0;
   out_958271563642232375[176] = 0;
   out_958271563642232375[177] = 0;
   out_958271563642232375[178] = 0;
   out_958271563642232375[179] = 0;
   out_958271563642232375[180] = 0;
   out_958271563642232375[181] = 0;
   out_958271563642232375[182] = 0;
   out_958271563642232375[183] = 0;
   out_958271563642232375[184] = 0;
   out_958271563642232375[185] = 0;
   out_958271563642232375[186] = 0;
   out_958271563642232375[187] = 0;
   out_958271563642232375[188] = 0;
   out_958271563642232375[189] = 0;
   out_958271563642232375[190] = 1;
   out_958271563642232375[191] = 0;
   out_958271563642232375[192] = 0;
   out_958271563642232375[193] = 0;
   out_958271563642232375[194] = 0;
   out_958271563642232375[195] = 0;
   out_958271563642232375[196] = 0;
   out_958271563642232375[197] = 0;
   out_958271563642232375[198] = 0;
   out_958271563642232375[199] = 0;
   out_958271563642232375[200] = 0;
   out_958271563642232375[201] = 0;
   out_958271563642232375[202] = 0;
   out_958271563642232375[203] = 0;
   out_958271563642232375[204] = 0;
   out_958271563642232375[205] = 0;
   out_958271563642232375[206] = 0;
   out_958271563642232375[207] = 0;
   out_958271563642232375[208] = 0;
   out_958271563642232375[209] = 1;
   out_958271563642232375[210] = 0;
   out_958271563642232375[211] = 0;
   out_958271563642232375[212] = 0;
   out_958271563642232375[213] = 0;
   out_958271563642232375[214] = 0;
   out_958271563642232375[215] = 0;
   out_958271563642232375[216] = 0;
   out_958271563642232375[217] = 0;
   out_958271563642232375[218] = 0;
   out_958271563642232375[219] = 0;
   out_958271563642232375[220] = 0;
   out_958271563642232375[221] = 0;
   out_958271563642232375[222] = 0;
   out_958271563642232375[223] = 0;
   out_958271563642232375[224] = 0;
   out_958271563642232375[225] = 0;
   out_958271563642232375[226] = 0;
   out_958271563642232375[227] = 0;
   out_958271563642232375[228] = 1;
   out_958271563642232375[229] = 0;
   out_958271563642232375[230] = 0;
   out_958271563642232375[231] = 0;
   out_958271563642232375[232] = 0;
   out_958271563642232375[233] = 0;
   out_958271563642232375[234] = 0;
   out_958271563642232375[235] = 0;
   out_958271563642232375[236] = 0;
   out_958271563642232375[237] = 0;
   out_958271563642232375[238] = 0;
   out_958271563642232375[239] = 0;
   out_958271563642232375[240] = 0;
   out_958271563642232375[241] = 0;
   out_958271563642232375[242] = 0;
   out_958271563642232375[243] = 0;
   out_958271563642232375[244] = 0;
   out_958271563642232375[245] = 0;
   out_958271563642232375[246] = 0;
   out_958271563642232375[247] = 1;
   out_958271563642232375[248] = 0;
   out_958271563642232375[249] = 0;
   out_958271563642232375[250] = 0;
   out_958271563642232375[251] = 0;
   out_958271563642232375[252] = 0;
   out_958271563642232375[253] = 0;
   out_958271563642232375[254] = 0;
   out_958271563642232375[255] = 0;
   out_958271563642232375[256] = 0;
   out_958271563642232375[257] = 0;
   out_958271563642232375[258] = 0;
   out_958271563642232375[259] = 0;
   out_958271563642232375[260] = 0;
   out_958271563642232375[261] = 0;
   out_958271563642232375[262] = 0;
   out_958271563642232375[263] = 0;
   out_958271563642232375[264] = 0;
   out_958271563642232375[265] = 0;
   out_958271563642232375[266] = 1;
   out_958271563642232375[267] = 0;
   out_958271563642232375[268] = 0;
   out_958271563642232375[269] = 0;
   out_958271563642232375[270] = 0;
   out_958271563642232375[271] = 0;
   out_958271563642232375[272] = 0;
   out_958271563642232375[273] = 0;
   out_958271563642232375[274] = 0;
   out_958271563642232375[275] = 0;
   out_958271563642232375[276] = 0;
   out_958271563642232375[277] = 0;
   out_958271563642232375[278] = 0;
   out_958271563642232375[279] = 0;
   out_958271563642232375[280] = 0;
   out_958271563642232375[281] = 0;
   out_958271563642232375[282] = 0;
   out_958271563642232375[283] = 0;
   out_958271563642232375[284] = 0;
   out_958271563642232375[285] = 1;
   out_958271563642232375[286] = 0;
   out_958271563642232375[287] = 0;
   out_958271563642232375[288] = 0;
   out_958271563642232375[289] = 0;
   out_958271563642232375[290] = 0;
   out_958271563642232375[291] = 0;
   out_958271563642232375[292] = 0;
   out_958271563642232375[293] = 0;
   out_958271563642232375[294] = 0;
   out_958271563642232375[295] = 0;
   out_958271563642232375[296] = 0;
   out_958271563642232375[297] = 0;
   out_958271563642232375[298] = 0;
   out_958271563642232375[299] = 0;
   out_958271563642232375[300] = 0;
   out_958271563642232375[301] = 0;
   out_958271563642232375[302] = 0;
   out_958271563642232375[303] = 0;
   out_958271563642232375[304] = 1;
   out_958271563642232375[305] = 0;
   out_958271563642232375[306] = 0;
   out_958271563642232375[307] = 0;
   out_958271563642232375[308] = 0;
   out_958271563642232375[309] = 0;
   out_958271563642232375[310] = 0;
   out_958271563642232375[311] = 0;
   out_958271563642232375[312] = 0;
   out_958271563642232375[313] = 0;
   out_958271563642232375[314] = 0;
   out_958271563642232375[315] = 0;
   out_958271563642232375[316] = 0;
   out_958271563642232375[317] = 0;
   out_958271563642232375[318] = 0;
   out_958271563642232375[319] = 0;
   out_958271563642232375[320] = 0;
   out_958271563642232375[321] = 0;
   out_958271563642232375[322] = 0;
   out_958271563642232375[323] = 1;
}
void h_4(double *state, double *unused, double *out_4832992228856902742) {
   out_4832992228856902742[0] = state[6] + state[9];
   out_4832992228856902742[1] = state[7] + state[10];
   out_4832992228856902742[2] = state[8] + state[11];
}
void H_4(double *state, double *unused, double *out_2408518913812250442) {
   out_2408518913812250442[0] = 0;
   out_2408518913812250442[1] = 0;
   out_2408518913812250442[2] = 0;
   out_2408518913812250442[3] = 0;
   out_2408518913812250442[4] = 0;
   out_2408518913812250442[5] = 0;
   out_2408518913812250442[6] = 1;
   out_2408518913812250442[7] = 0;
   out_2408518913812250442[8] = 0;
   out_2408518913812250442[9] = 1;
   out_2408518913812250442[10] = 0;
   out_2408518913812250442[11] = 0;
   out_2408518913812250442[12] = 0;
   out_2408518913812250442[13] = 0;
   out_2408518913812250442[14] = 0;
   out_2408518913812250442[15] = 0;
   out_2408518913812250442[16] = 0;
   out_2408518913812250442[17] = 0;
   out_2408518913812250442[18] = 0;
   out_2408518913812250442[19] = 0;
   out_2408518913812250442[20] = 0;
   out_2408518913812250442[21] = 0;
   out_2408518913812250442[22] = 0;
   out_2408518913812250442[23] = 0;
   out_2408518913812250442[24] = 0;
   out_2408518913812250442[25] = 1;
   out_2408518913812250442[26] = 0;
   out_2408518913812250442[27] = 0;
   out_2408518913812250442[28] = 1;
   out_2408518913812250442[29] = 0;
   out_2408518913812250442[30] = 0;
   out_2408518913812250442[31] = 0;
   out_2408518913812250442[32] = 0;
   out_2408518913812250442[33] = 0;
   out_2408518913812250442[34] = 0;
   out_2408518913812250442[35] = 0;
   out_2408518913812250442[36] = 0;
   out_2408518913812250442[37] = 0;
   out_2408518913812250442[38] = 0;
   out_2408518913812250442[39] = 0;
   out_2408518913812250442[40] = 0;
   out_2408518913812250442[41] = 0;
   out_2408518913812250442[42] = 0;
   out_2408518913812250442[43] = 0;
   out_2408518913812250442[44] = 1;
   out_2408518913812250442[45] = 0;
   out_2408518913812250442[46] = 0;
   out_2408518913812250442[47] = 1;
   out_2408518913812250442[48] = 0;
   out_2408518913812250442[49] = 0;
   out_2408518913812250442[50] = 0;
   out_2408518913812250442[51] = 0;
   out_2408518913812250442[52] = 0;
   out_2408518913812250442[53] = 0;
}
void h_10(double *state, double *unused, double *out_3497927463584229027) {
   out_3497927463584229027[0] = 9.8100000000000005*sin(state[1]) - state[4]*state[8] + state[5]*state[7] + state[12] + state[15];
   out_3497927463584229027[1] = -9.8100000000000005*sin(state[0])*cos(state[1]) + state[3]*state[8] - state[5]*state[6] + state[13] + state[16];
   out_3497927463584229027[2] = -9.8100000000000005*cos(state[0])*cos(state[1]) - state[3]*state[7] + state[4]*state[6] + state[14] + state[17];
}
void H_10(double *state, double *unused, double *out_4949237892416765352) {
   out_4949237892416765352[0] = 0;
   out_4949237892416765352[1] = 9.8100000000000005*cos(state[1]);
   out_4949237892416765352[2] = 0;
   out_4949237892416765352[3] = 0;
   out_4949237892416765352[4] = -state[8];
   out_4949237892416765352[5] = state[7];
   out_4949237892416765352[6] = 0;
   out_4949237892416765352[7] = state[5];
   out_4949237892416765352[8] = -state[4];
   out_4949237892416765352[9] = 0;
   out_4949237892416765352[10] = 0;
   out_4949237892416765352[11] = 0;
   out_4949237892416765352[12] = 1;
   out_4949237892416765352[13] = 0;
   out_4949237892416765352[14] = 0;
   out_4949237892416765352[15] = 1;
   out_4949237892416765352[16] = 0;
   out_4949237892416765352[17] = 0;
   out_4949237892416765352[18] = -9.8100000000000005*cos(state[0])*cos(state[1]);
   out_4949237892416765352[19] = 9.8100000000000005*sin(state[0])*sin(state[1]);
   out_4949237892416765352[20] = 0;
   out_4949237892416765352[21] = state[8];
   out_4949237892416765352[22] = 0;
   out_4949237892416765352[23] = -state[6];
   out_4949237892416765352[24] = -state[5];
   out_4949237892416765352[25] = 0;
   out_4949237892416765352[26] = state[3];
   out_4949237892416765352[27] = 0;
   out_4949237892416765352[28] = 0;
   out_4949237892416765352[29] = 0;
   out_4949237892416765352[30] = 0;
   out_4949237892416765352[31] = 1;
   out_4949237892416765352[32] = 0;
   out_4949237892416765352[33] = 0;
   out_4949237892416765352[34] = 1;
   out_4949237892416765352[35] = 0;
   out_4949237892416765352[36] = 9.8100000000000005*sin(state[0])*cos(state[1]);
   out_4949237892416765352[37] = 9.8100000000000005*sin(state[1])*cos(state[0]);
   out_4949237892416765352[38] = 0;
   out_4949237892416765352[39] = -state[7];
   out_4949237892416765352[40] = state[6];
   out_4949237892416765352[41] = 0;
   out_4949237892416765352[42] = state[4];
   out_4949237892416765352[43] = -state[3];
   out_4949237892416765352[44] = 0;
   out_4949237892416765352[45] = 0;
   out_4949237892416765352[46] = 0;
   out_4949237892416765352[47] = 0;
   out_4949237892416765352[48] = 0;
   out_4949237892416765352[49] = 0;
   out_4949237892416765352[50] = 1;
   out_4949237892416765352[51] = 0;
   out_4949237892416765352[52] = 0;
   out_4949237892416765352[53] = 1;
}
void h_13(double *state, double *unused, double *out_7372319986312258601) {
   out_7372319986312258601[0] = state[3];
   out_7372319986312258601[1] = state[4];
   out_7372319986312258601[2] = state[5];
}
void H_13(double *state, double *unused, double *out_803754911520082359) {
   out_803754911520082359[0] = 0;
   out_803754911520082359[1] = 0;
   out_803754911520082359[2] = 0;
   out_803754911520082359[3] = 1;
   out_803754911520082359[4] = 0;
   out_803754911520082359[5] = 0;
   out_803754911520082359[6] = 0;
   out_803754911520082359[7] = 0;
   out_803754911520082359[8] = 0;
   out_803754911520082359[9] = 0;
   out_803754911520082359[10] = 0;
   out_803754911520082359[11] = 0;
   out_803754911520082359[12] = 0;
   out_803754911520082359[13] = 0;
   out_803754911520082359[14] = 0;
   out_803754911520082359[15] = 0;
   out_803754911520082359[16] = 0;
   out_803754911520082359[17] = 0;
   out_803754911520082359[18] = 0;
   out_803754911520082359[19] = 0;
   out_803754911520082359[20] = 0;
   out_803754911520082359[21] = 0;
   out_803754911520082359[22] = 1;
   out_803754911520082359[23] = 0;
   out_803754911520082359[24] = 0;
   out_803754911520082359[25] = 0;
   out_803754911520082359[26] = 0;
   out_803754911520082359[27] = 0;
   out_803754911520082359[28] = 0;
   out_803754911520082359[29] = 0;
   out_803754911520082359[30] = 0;
   out_803754911520082359[31] = 0;
   out_803754911520082359[32] = 0;
   out_803754911520082359[33] = 0;
   out_803754911520082359[34] = 0;
   out_803754911520082359[35] = 0;
   out_803754911520082359[36] = 0;
   out_803754911520082359[37] = 0;
   out_803754911520082359[38] = 0;
   out_803754911520082359[39] = 0;
   out_803754911520082359[40] = 0;
   out_803754911520082359[41] = 1;
   out_803754911520082359[42] = 0;
   out_803754911520082359[43] = 0;
   out_803754911520082359[44] = 0;
   out_803754911520082359[45] = 0;
   out_803754911520082359[46] = 0;
   out_803754911520082359[47] = 0;
   out_803754911520082359[48] = 0;
   out_803754911520082359[49] = 0;
   out_803754911520082359[50] = 0;
   out_803754911520082359[51] = 0;
   out_803754911520082359[52] = 0;
   out_803754911520082359[53] = 0;
}
void h_14(double *state, double *unused, double *out_1827110187090498104) {
   out_1827110187090498104[0] = state[6];
   out_1827110187090498104[1] = state[7];
   out_1827110187090498104[2] = state[8];
}
void H_14(double *state, double *unused, double *out_1554721942527234087) {
   out_1554721942527234087[0] = 0;
   out_1554721942527234087[1] = 0;
   out_1554721942527234087[2] = 0;
   out_1554721942527234087[3] = 0;
   out_1554721942527234087[4] = 0;
   out_1554721942527234087[5] = 0;
   out_1554721942527234087[6] = 1;
   out_1554721942527234087[7] = 0;
   out_1554721942527234087[8] = 0;
   out_1554721942527234087[9] = 0;
   out_1554721942527234087[10] = 0;
   out_1554721942527234087[11] = 0;
   out_1554721942527234087[12] = 0;
   out_1554721942527234087[13] = 0;
   out_1554721942527234087[14] = 0;
   out_1554721942527234087[15] = 0;
   out_1554721942527234087[16] = 0;
   out_1554721942527234087[17] = 0;
   out_1554721942527234087[18] = 0;
   out_1554721942527234087[19] = 0;
   out_1554721942527234087[20] = 0;
   out_1554721942527234087[21] = 0;
   out_1554721942527234087[22] = 0;
   out_1554721942527234087[23] = 0;
   out_1554721942527234087[24] = 0;
   out_1554721942527234087[25] = 1;
   out_1554721942527234087[26] = 0;
   out_1554721942527234087[27] = 0;
   out_1554721942527234087[28] = 0;
   out_1554721942527234087[29] = 0;
   out_1554721942527234087[30] = 0;
   out_1554721942527234087[31] = 0;
   out_1554721942527234087[32] = 0;
   out_1554721942527234087[33] = 0;
   out_1554721942527234087[34] = 0;
   out_1554721942527234087[35] = 0;
   out_1554721942527234087[36] = 0;
   out_1554721942527234087[37] = 0;
   out_1554721942527234087[38] = 0;
   out_1554721942527234087[39] = 0;
   out_1554721942527234087[40] = 0;
   out_1554721942527234087[41] = 0;
   out_1554721942527234087[42] = 0;
   out_1554721942527234087[43] = 0;
   out_1554721942527234087[44] = 1;
   out_1554721942527234087[45] = 0;
   out_1554721942527234087[46] = 0;
   out_1554721942527234087[47] = 0;
   out_1554721942527234087[48] = 0;
   out_1554721942527234087[49] = 0;
   out_1554721942527234087[50] = 0;
   out_1554721942527234087[51] = 0;
   out_1554721942527234087[52] = 0;
   out_1554721942527234087[53] = 0;
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
void pose_err_fun(double *nom_x, double *delta_x, double *out_7616755969345465164) {
  err_fun(nom_x, delta_x, out_7616755969345465164);
}
void pose_inv_err_fun(double *nom_x, double *true_x, double *out_2983579217144166569) {
  inv_err_fun(nom_x, true_x, out_2983579217144166569);
}
void pose_H_mod_fun(double *state, double *out_7561037298851331177) {
  H_mod_fun(state, out_7561037298851331177);
}
void pose_f_fun(double *state, double dt, double *out_5713485962747764656) {
  f_fun(state,  dt, out_5713485962747764656);
}
void pose_F_fun(double *state, double dt, double *out_958271563642232375) {
  F_fun(state,  dt, out_958271563642232375);
}
void pose_h_4(double *state, double *unused, double *out_4832992228856902742) {
  h_4(state, unused, out_4832992228856902742);
}
void pose_H_4(double *state, double *unused, double *out_2408518913812250442) {
  H_4(state, unused, out_2408518913812250442);
}
void pose_h_10(double *state, double *unused, double *out_3497927463584229027) {
  h_10(state, unused, out_3497927463584229027);
}
void pose_H_10(double *state, double *unused, double *out_4949237892416765352) {
  H_10(state, unused, out_4949237892416765352);
}
void pose_h_13(double *state, double *unused, double *out_7372319986312258601) {
  h_13(state, unused, out_7372319986312258601);
}
void pose_H_13(double *state, double *unused, double *out_803754911520082359) {
  H_13(state, unused, out_803754911520082359);
}
void pose_h_14(double *state, double *unused, double *out_1827110187090498104) {
  h_14(state, unused, out_1827110187090498104);
}
void pose_H_14(double *state, double *unused, double *out_1554721942527234087) {
  H_14(state, unused, out_1554721942527234087);
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
