#include "car.h"

namespace {
#define DIM 9
#define EDIM 9
#define MEDIM 9
typedef void (*Hfun)(double *, double *, double *);

double mass;

void set_mass(double x){ mass = x;}

double rotational_inertia;

void set_rotational_inertia(double x){ rotational_inertia = x;}

double center_to_front;

void set_center_to_front(double x){ center_to_front = x;}

double center_to_rear;

void set_center_to_rear(double x){ center_to_rear = x;}

double stiffness_front;

void set_stiffness_front(double x){ stiffness_front = x;}

double stiffness_rear;

void set_stiffness_rear(double x){ stiffness_rear = x;}
const static double MAHA_THRESH_25 = 3.8414588206941227;
const static double MAHA_THRESH_24 = 5.991464547107981;
const static double MAHA_THRESH_30 = 3.8414588206941227;
const static double MAHA_THRESH_26 = 3.8414588206941227;
const static double MAHA_THRESH_27 = 3.8414588206941227;
const static double MAHA_THRESH_29 = 3.8414588206941227;
const static double MAHA_THRESH_28 = 3.8414588206941227;
const static double MAHA_THRESH_31 = 3.8414588206941227;

/******************************************************************************
 *                      Code generated with SymPy 1.14.0                      *
 *                                                                            *
 *              See http://www.sympy.org/ for more information.               *
 *                                                                            *
 *                         This file is part of 'ekf'                         *
 ******************************************************************************/
void err_fun(double *nom_x, double *delta_x, double *out_6104712207101523759) {
   out_6104712207101523759[0] = delta_x[0] + nom_x[0];
   out_6104712207101523759[1] = delta_x[1] + nom_x[1];
   out_6104712207101523759[2] = delta_x[2] + nom_x[2];
   out_6104712207101523759[3] = delta_x[3] + nom_x[3];
   out_6104712207101523759[4] = delta_x[4] + nom_x[4];
   out_6104712207101523759[5] = delta_x[5] + nom_x[5];
   out_6104712207101523759[6] = delta_x[6] + nom_x[6];
   out_6104712207101523759[7] = delta_x[7] + nom_x[7];
   out_6104712207101523759[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_4901417542031613009) {
   out_4901417542031613009[0] = -nom_x[0] + true_x[0];
   out_4901417542031613009[1] = -nom_x[1] + true_x[1];
   out_4901417542031613009[2] = -nom_x[2] + true_x[2];
   out_4901417542031613009[3] = -nom_x[3] + true_x[3];
   out_4901417542031613009[4] = -nom_x[4] + true_x[4];
   out_4901417542031613009[5] = -nom_x[5] + true_x[5];
   out_4901417542031613009[6] = -nom_x[6] + true_x[6];
   out_4901417542031613009[7] = -nom_x[7] + true_x[7];
   out_4901417542031613009[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_4051006717071082906) {
   out_4051006717071082906[0] = 1.0;
   out_4051006717071082906[1] = 0.0;
   out_4051006717071082906[2] = 0.0;
   out_4051006717071082906[3] = 0.0;
   out_4051006717071082906[4] = 0.0;
   out_4051006717071082906[5] = 0.0;
   out_4051006717071082906[6] = 0.0;
   out_4051006717071082906[7] = 0.0;
   out_4051006717071082906[8] = 0.0;
   out_4051006717071082906[9] = 0.0;
   out_4051006717071082906[10] = 1.0;
   out_4051006717071082906[11] = 0.0;
   out_4051006717071082906[12] = 0.0;
   out_4051006717071082906[13] = 0.0;
   out_4051006717071082906[14] = 0.0;
   out_4051006717071082906[15] = 0.0;
   out_4051006717071082906[16] = 0.0;
   out_4051006717071082906[17] = 0.0;
   out_4051006717071082906[18] = 0.0;
   out_4051006717071082906[19] = 0.0;
   out_4051006717071082906[20] = 1.0;
   out_4051006717071082906[21] = 0.0;
   out_4051006717071082906[22] = 0.0;
   out_4051006717071082906[23] = 0.0;
   out_4051006717071082906[24] = 0.0;
   out_4051006717071082906[25] = 0.0;
   out_4051006717071082906[26] = 0.0;
   out_4051006717071082906[27] = 0.0;
   out_4051006717071082906[28] = 0.0;
   out_4051006717071082906[29] = 0.0;
   out_4051006717071082906[30] = 1.0;
   out_4051006717071082906[31] = 0.0;
   out_4051006717071082906[32] = 0.0;
   out_4051006717071082906[33] = 0.0;
   out_4051006717071082906[34] = 0.0;
   out_4051006717071082906[35] = 0.0;
   out_4051006717071082906[36] = 0.0;
   out_4051006717071082906[37] = 0.0;
   out_4051006717071082906[38] = 0.0;
   out_4051006717071082906[39] = 0.0;
   out_4051006717071082906[40] = 1.0;
   out_4051006717071082906[41] = 0.0;
   out_4051006717071082906[42] = 0.0;
   out_4051006717071082906[43] = 0.0;
   out_4051006717071082906[44] = 0.0;
   out_4051006717071082906[45] = 0.0;
   out_4051006717071082906[46] = 0.0;
   out_4051006717071082906[47] = 0.0;
   out_4051006717071082906[48] = 0.0;
   out_4051006717071082906[49] = 0.0;
   out_4051006717071082906[50] = 1.0;
   out_4051006717071082906[51] = 0.0;
   out_4051006717071082906[52] = 0.0;
   out_4051006717071082906[53] = 0.0;
   out_4051006717071082906[54] = 0.0;
   out_4051006717071082906[55] = 0.0;
   out_4051006717071082906[56] = 0.0;
   out_4051006717071082906[57] = 0.0;
   out_4051006717071082906[58] = 0.0;
   out_4051006717071082906[59] = 0.0;
   out_4051006717071082906[60] = 1.0;
   out_4051006717071082906[61] = 0.0;
   out_4051006717071082906[62] = 0.0;
   out_4051006717071082906[63] = 0.0;
   out_4051006717071082906[64] = 0.0;
   out_4051006717071082906[65] = 0.0;
   out_4051006717071082906[66] = 0.0;
   out_4051006717071082906[67] = 0.0;
   out_4051006717071082906[68] = 0.0;
   out_4051006717071082906[69] = 0.0;
   out_4051006717071082906[70] = 1.0;
   out_4051006717071082906[71] = 0.0;
   out_4051006717071082906[72] = 0.0;
   out_4051006717071082906[73] = 0.0;
   out_4051006717071082906[74] = 0.0;
   out_4051006717071082906[75] = 0.0;
   out_4051006717071082906[76] = 0.0;
   out_4051006717071082906[77] = 0.0;
   out_4051006717071082906[78] = 0.0;
   out_4051006717071082906[79] = 0.0;
   out_4051006717071082906[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_3418974710290228612) {
   out_3418974710290228612[0] = state[0];
   out_3418974710290228612[1] = state[1];
   out_3418974710290228612[2] = state[2];
   out_3418974710290228612[3] = state[3];
   out_3418974710290228612[4] = state[4];
   out_3418974710290228612[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_3418974710290228612[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_3418974710290228612[7] = state[7];
   out_3418974710290228612[8] = state[8];
}
void F_fun(double *state, double dt, double *out_3699468657963228141) {
   out_3699468657963228141[0] = 1;
   out_3699468657963228141[1] = 0;
   out_3699468657963228141[2] = 0;
   out_3699468657963228141[3] = 0;
   out_3699468657963228141[4] = 0;
   out_3699468657963228141[5] = 0;
   out_3699468657963228141[6] = 0;
   out_3699468657963228141[7] = 0;
   out_3699468657963228141[8] = 0;
   out_3699468657963228141[9] = 0;
   out_3699468657963228141[10] = 1;
   out_3699468657963228141[11] = 0;
   out_3699468657963228141[12] = 0;
   out_3699468657963228141[13] = 0;
   out_3699468657963228141[14] = 0;
   out_3699468657963228141[15] = 0;
   out_3699468657963228141[16] = 0;
   out_3699468657963228141[17] = 0;
   out_3699468657963228141[18] = 0;
   out_3699468657963228141[19] = 0;
   out_3699468657963228141[20] = 1;
   out_3699468657963228141[21] = 0;
   out_3699468657963228141[22] = 0;
   out_3699468657963228141[23] = 0;
   out_3699468657963228141[24] = 0;
   out_3699468657963228141[25] = 0;
   out_3699468657963228141[26] = 0;
   out_3699468657963228141[27] = 0;
   out_3699468657963228141[28] = 0;
   out_3699468657963228141[29] = 0;
   out_3699468657963228141[30] = 1;
   out_3699468657963228141[31] = 0;
   out_3699468657963228141[32] = 0;
   out_3699468657963228141[33] = 0;
   out_3699468657963228141[34] = 0;
   out_3699468657963228141[35] = 0;
   out_3699468657963228141[36] = 0;
   out_3699468657963228141[37] = 0;
   out_3699468657963228141[38] = 0;
   out_3699468657963228141[39] = 0;
   out_3699468657963228141[40] = 1;
   out_3699468657963228141[41] = 0;
   out_3699468657963228141[42] = 0;
   out_3699468657963228141[43] = 0;
   out_3699468657963228141[44] = 0;
   out_3699468657963228141[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_3699468657963228141[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_3699468657963228141[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_3699468657963228141[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_3699468657963228141[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_3699468657963228141[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_3699468657963228141[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_3699468657963228141[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_3699468657963228141[53] = -9.8100000000000005*dt;
   out_3699468657963228141[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_3699468657963228141[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_3699468657963228141[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_3699468657963228141[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_3699468657963228141[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_3699468657963228141[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_3699468657963228141[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_3699468657963228141[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_3699468657963228141[62] = 0;
   out_3699468657963228141[63] = 0;
   out_3699468657963228141[64] = 0;
   out_3699468657963228141[65] = 0;
   out_3699468657963228141[66] = 0;
   out_3699468657963228141[67] = 0;
   out_3699468657963228141[68] = 0;
   out_3699468657963228141[69] = 0;
   out_3699468657963228141[70] = 1;
   out_3699468657963228141[71] = 0;
   out_3699468657963228141[72] = 0;
   out_3699468657963228141[73] = 0;
   out_3699468657963228141[74] = 0;
   out_3699468657963228141[75] = 0;
   out_3699468657963228141[76] = 0;
   out_3699468657963228141[77] = 0;
   out_3699468657963228141[78] = 0;
   out_3699468657963228141[79] = 0;
   out_3699468657963228141[80] = 1;
}
void h_25(double *state, double *unused, double *out_7881868868211418241) {
   out_7881868868211418241[0] = state[6];
}
void H_25(double *state, double *unused, double *out_7573987367060574583) {
   out_7573987367060574583[0] = 0;
   out_7573987367060574583[1] = 0;
   out_7573987367060574583[2] = 0;
   out_7573987367060574583[3] = 0;
   out_7573987367060574583[4] = 0;
   out_7573987367060574583[5] = 0;
   out_7573987367060574583[6] = 1;
   out_7573987367060574583[7] = 0;
   out_7573987367060574583[8] = 0;
}
void h_24(double *state, double *unused, double *out_6965493433416690101) {
   out_6965493433416690101[0] = state[4];
   out_6965493433416690101[1] = state[5];
}
void H_24(double *state, double *unused, double *out_7314831107846653897) {
   out_7314831107846653897[0] = 0;
   out_7314831107846653897[1] = 0;
   out_7314831107846653897[2] = 0;
   out_7314831107846653897[3] = 0;
   out_7314831107846653897[4] = 1;
   out_7314831107846653897[5] = 0;
   out_7314831107846653897[6] = 0;
   out_7314831107846653897[7] = 0;
   out_7314831107846653897[8] = 0;
   out_7314831107846653897[9] = 0;
   out_7314831107846653897[10] = 0;
   out_7314831107846653897[11] = 0;
   out_7314831107846653897[12] = 0;
   out_7314831107846653897[13] = 0;
   out_7314831107846653897[14] = 1;
   out_7314831107846653897[15] = 0;
   out_7314831107846653897[16] = 0;
   out_7314831107846653897[17] = 0;
}
void h_30(double *state, double *unused, double *out_5527754398725254445) {
   out_5527754398725254445[0] = state[4];
}
void H_30(double *state, double *unused, double *out_8354423748141728406) {
   out_8354423748141728406[0] = 0;
   out_8354423748141728406[1] = 0;
   out_8354423748141728406[2] = 0;
   out_8354423748141728406[3] = 0;
   out_8354423748141728406[4] = 1;
   out_8354423748141728406[5] = 0;
   out_8354423748141728406[6] = 0;
   out_8354423748141728406[7] = 0;
   out_8354423748141728406[8] = 0;
}
void h_26(double *state, double *unused, double *out_4047826294150907485) {
   out_4047826294150907485[0] = state[7];
}
void H_26(double *state, double *unused, double *out_3832484048186518359) {
   out_3832484048186518359[0] = 0;
   out_3832484048186518359[1] = 0;
   out_3832484048186518359[2] = 0;
   out_3832484048186518359[3] = 0;
   out_3832484048186518359[4] = 0;
   out_3832484048186518359[5] = 0;
   out_3832484048186518359[6] = 0;
   out_3832484048186518359[7] = 1;
   out_3832484048186518359[8] = 0;
}
void h_27(double *state, double *unused, double *out_7960469884689435724) {
   out_7960469884689435724[0] = state[3];
}
void H_27(double *state, double *unused, double *out_6130829676957785189) {
   out_6130829676957785189[0] = 0;
   out_6130829676957785189[1] = 0;
   out_6130829676957785189[2] = 0;
   out_6130829676957785189[3] = 1;
   out_6130829676957785189[4] = 0;
   out_6130829676957785189[5] = 0;
   out_6130829676957785189[6] = 0;
   out_6130829676957785189[7] = 0;
   out_6130829676957785189[8] = 0;
}
void h_29(double *state, double *unused, double *out_4330826993179455763) {
   out_4330826993179455763[0] = state[1];
}
void H_29(double *state, double *unused, double *out_7844192403827336222) {
   out_7844192403827336222[0] = 0;
   out_7844192403827336222[1] = 1;
   out_7844192403827336222[2] = 0;
   out_7844192403827336222[3] = 0;
   out_7844192403827336222[4] = 0;
   out_7844192403827336222[5] = 0;
   out_7844192403827336222[6] = 0;
   out_7844192403827336222[7] = 0;
   out_7844192403827336222[8] = 0;
}
void h_28(double *state, double *unused, double *out_8563785769365913241) {
   out_8563785769365913241[0] = state[0];
}
void H_28(double *state, double *unused, double *out_5520152652812684820) {
   out_5520152652812684820[0] = 1;
   out_5520152652812684820[1] = 0;
   out_5520152652812684820[2] = 0;
   out_5520152652812684820[3] = 0;
   out_5520152652812684820[4] = 0;
   out_5520152652812684820[5] = 0;
   out_5520152652812684820[6] = 0;
   out_5520152652812684820[7] = 0;
   out_5520152652812684820[8] = 0;
}
void h_31(double *state, double *unused, double *out_6703191729069631723) {
   out_6703191729069631723[0] = state[8];
}
void H_31(double *state, double *unused, double *out_7604633328937535011) {
   out_7604633328937535011[0] = 0;
   out_7604633328937535011[1] = 0;
   out_7604633328937535011[2] = 0;
   out_7604633328937535011[3] = 0;
   out_7604633328937535011[4] = 0;
   out_7604633328937535011[5] = 0;
   out_7604633328937535011[6] = 0;
   out_7604633328937535011[7] = 0;
   out_7604633328937535011[8] = 1;
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

void car_update_25(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_25, H_25, NULL, in_z, in_R, in_ea, MAHA_THRESH_25);
}
void car_update_24(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<2, 3, 0>(in_x, in_P, h_24, H_24, NULL, in_z, in_R, in_ea, MAHA_THRESH_24);
}
void car_update_30(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_30, H_30, NULL, in_z, in_R, in_ea, MAHA_THRESH_30);
}
void car_update_26(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_26, H_26, NULL, in_z, in_R, in_ea, MAHA_THRESH_26);
}
void car_update_27(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_27, H_27, NULL, in_z, in_R, in_ea, MAHA_THRESH_27);
}
void car_update_29(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_29, H_29, NULL, in_z, in_R, in_ea, MAHA_THRESH_29);
}
void car_update_28(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_28, H_28, NULL, in_z, in_R, in_ea, MAHA_THRESH_28);
}
void car_update_31(double *in_x, double *in_P, double *in_z, double *in_R, double *in_ea) {
  update<1, 3, 0>(in_x, in_P, h_31, H_31, NULL, in_z, in_R, in_ea, MAHA_THRESH_31);
}
void car_err_fun(double *nom_x, double *delta_x, double *out_6104712207101523759) {
  err_fun(nom_x, delta_x, out_6104712207101523759);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_4901417542031613009) {
  inv_err_fun(nom_x, true_x, out_4901417542031613009);
}
void car_H_mod_fun(double *state, double *out_4051006717071082906) {
  H_mod_fun(state, out_4051006717071082906);
}
void car_f_fun(double *state, double dt, double *out_3418974710290228612) {
  f_fun(state,  dt, out_3418974710290228612);
}
void car_F_fun(double *state, double dt, double *out_3699468657963228141) {
  F_fun(state,  dt, out_3699468657963228141);
}
void car_h_25(double *state, double *unused, double *out_7881868868211418241) {
  h_25(state, unused, out_7881868868211418241);
}
void car_H_25(double *state, double *unused, double *out_7573987367060574583) {
  H_25(state, unused, out_7573987367060574583);
}
void car_h_24(double *state, double *unused, double *out_6965493433416690101) {
  h_24(state, unused, out_6965493433416690101);
}
void car_H_24(double *state, double *unused, double *out_7314831107846653897) {
  H_24(state, unused, out_7314831107846653897);
}
void car_h_30(double *state, double *unused, double *out_5527754398725254445) {
  h_30(state, unused, out_5527754398725254445);
}
void car_H_30(double *state, double *unused, double *out_8354423748141728406) {
  H_30(state, unused, out_8354423748141728406);
}
void car_h_26(double *state, double *unused, double *out_4047826294150907485) {
  h_26(state, unused, out_4047826294150907485);
}
void car_H_26(double *state, double *unused, double *out_3832484048186518359) {
  H_26(state, unused, out_3832484048186518359);
}
void car_h_27(double *state, double *unused, double *out_7960469884689435724) {
  h_27(state, unused, out_7960469884689435724);
}
void car_H_27(double *state, double *unused, double *out_6130829676957785189) {
  H_27(state, unused, out_6130829676957785189);
}
void car_h_29(double *state, double *unused, double *out_4330826993179455763) {
  h_29(state, unused, out_4330826993179455763);
}
void car_H_29(double *state, double *unused, double *out_7844192403827336222) {
  H_29(state, unused, out_7844192403827336222);
}
void car_h_28(double *state, double *unused, double *out_8563785769365913241) {
  h_28(state, unused, out_8563785769365913241);
}
void car_H_28(double *state, double *unused, double *out_5520152652812684820) {
  H_28(state, unused, out_5520152652812684820);
}
void car_h_31(double *state, double *unused, double *out_6703191729069631723) {
  h_31(state, unused, out_6703191729069631723);
}
void car_H_31(double *state, double *unused, double *out_7604633328937535011) {
  H_31(state, unused, out_7604633328937535011);
}
void car_predict(double *in_x, double *in_P, double *in_Q, double dt) {
  predict(in_x, in_P, in_Q, dt);
}
void car_set_mass(double x) {
  set_mass(x);
}
void car_set_rotational_inertia(double x) {
  set_rotational_inertia(x);
}
void car_set_center_to_front(double x) {
  set_center_to_front(x);
}
void car_set_center_to_rear(double x) {
  set_center_to_rear(x);
}
void car_set_stiffness_front(double x) {
  set_stiffness_front(x);
}
void car_set_stiffness_rear(double x) {
  set_stiffness_rear(x);
}
}

const EKF car = {
  .name = "car",
  .kinds = { 25, 24, 30, 26, 27, 29, 28, 31 },
  .feature_kinds = {  },
  .f_fun = car_f_fun,
  .F_fun = car_F_fun,
  .err_fun = car_err_fun,
  .inv_err_fun = car_inv_err_fun,
  .H_mod_fun = car_H_mod_fun,
  .predict = car_predict,
  .hs = {
    { 25, car_h_25 },
    { 24, car_h_24 },
    { 30, car_h_30 },
    { 26, car_h_26 },
    { 27, car_h_27 },
    { 29, car_h_29 },
    { 28, car_h_28 },
    { 31, car_h_31 },
  },
  .Hs = {
    { 25, car_H_25 },
    { 24, car_H_24 },
    { 30, car_H_30 },
    { 26, car_H_26 },
    { 27, car_H_27 },
    { 29, car_H_29 },
    { 28, car_H_28 },
    { 31, car_H_31 },
  },
  .updates = {
    { 25, car_update_25 },
    { 24, car_update_24 },
    { 30, car_update_30 },
    { 26, car_update_26 },
    { 27, car_update_27 },
    { 29, car_update_29 },
    { 28, car_update_28 },
    { 31, car_update_31 },
  },
  .Hes = {
  },
  .sets = {
    { "mass", car_set_mass },
    { "rotational_inertia", car_set_rotational_inertia },
    { "center_to_front", car_set_center_to_front },
    { "center_to_rear", car_set_center_to_rear },
    { "stiffness_front", car_set_stiffness_front },
    { "stiffness_rear", car_set_stiffness_rear },
  },
  .extra_routines = {
  },
};

ekf_lib_init(car)
