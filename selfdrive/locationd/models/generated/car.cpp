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
void err_fun(double *nom_x, double *delta_x, double *out_1176760182641486560) {
   out_1176760182641486560[0] = delta_x[0] + nom_x[0];
   out_1176760182641486560[1] = delta_x[1] + nom_x[1];
   out_1176760182641486560[2] = delta_x[2] + nom_x[2];
   out_1176760182641486560[3] = delta_x[3] + nom_x[3];
   out_1176760182641486560[4] = delta_x[4] + nom_x[4];
   out_1176760182641486560[5] = delta_x[5] + nom_x[5];
   out_1176760182641486560[6] = delta_x[6] + nom_x[6];
   out_1176760182641486560[7] = delta_x[7] + nom_x[7];
   out_1176760182641486560[8] = delta_x[8] + nom_x[8];
}
void inv_err_fun(double *nom_x, double *true_x, double *out_2893373232090748310) {
   out_2893373232090748310[0] = -nom_x[0] + true_x[0];
   out_2893373232090748310[1] = -nom_x[1] + true_x[1];
   out_2893373232090748310[2] = -nom_x[2] + true_x[2];
   out_2893373232090748310[3] = -nom_x[3] + true_x[3];
   out_2893373232090748310[4] = -nom_x[4] + true_x[4];
   out_2893373232090748310[5] = -nom_x[5] + true_x[5];
   out_2893373232090748310[6] = -nom_x[6] + true_x[6];
   out_2893373232090748310[7] = -nom_x[7] + true_x[7];
   out_2893373232090748310[8] = -nom_x[8] + true_x[8];
}
void H_mod_fun(double *state, double *out_2729823001511069589) {
   out_2729823001511069589[0] = 1.0;
   out_2729823001511069589[1] = 0.0;
   out_2729823001511069589[2] = 0.0;
   out_2729823001511069589[3] = 0.0;
   out_2729823001511069589[4] = 0.0;
   out_2729823001511069589[5] = 0.0;
   out_2729823001511069589[6] = 0.0;
   out_2729823001511069589[7] = 0.0;
   out_2729823001511069589[8] = 0.0;
   out_2729823001511069589[9] = 0.0;
   out_2729823001511069589[10] = 1.0;
   out_2729823001511069589[11] = 0.0;
   out_2729823001511069589[12] = 0.0;
   out_2729823001511069589[13] = 0.0;
   out_2729823001511069589[14] = 0.0;
   out_2729823001511069589[15] = 0.0;
   out_2729823001511069589[16] = 0.0;
   out_2729823001511069589[17] = 0.0;
   out_2729823001511069589[18] = 0.0;
   out_2729823001511069589[19] = 0.0;
   out_2729823001511069589[20] = 1.0;
   out_2729823001511069589[21] = 0.0;
   out_2729823001511069589[22] = 0.0;
   out_2729823001511069589[23] = 0.0;
   out_2729823001511069589[24] = 0.0;
   out_2729823001511069589[25] = 0.0;
   out_2729823001511069589[26] = 0.0;
   out_2729823001511069589[27] = 0.0;
   out_2729823001511069589[28] = 0.0;
   out_2729823001511069589[29] = 0.0;
   out_2729823001511069589[30] = 1.0;
   out_2729823001511069589[31] = 0.0;
   out_2729823001511069589[32] = 0.0;
   out_2729823001511069589[33] = 0.0;
   out_2729823001511069589[34] = 0.0;
   out_2729823001511069589[35] = 0.0;
   out_2729823001511069589[36] = 0.0;
   out_2729823001511069589[37] = 0.0;
   out_2729823001511069589[38] = 0.0;
   out_2729823001511069589[39] = 0.0;
   out_2729823001511069589[40] = 1.0;
   out_2729823001511069589[41] = 0.0;
   out_2729823001511069589[42] = 0.0;
   out_2729823001511069589[43] = 0.0;
   out_2729823001511069589[44] = 0.0;
   out_2729823001511069589[45] = 0.0;
   out_2729823001511069589[46] = 0.0;
   out_2729823001511069589[47] = 0.0;
   out_2729823001511069589[48] = 0.0;
   out_2729823001511069589[49] = 0.0;
   out_2729823001511069589[50] = 1.0;
   out_2729823001511069589[51] = 0.0;
   out_2729823001511069589[52] = 0.0;
   out_2729823001511069589[53] = 0.0;
   out_2729823001511069589[54] = 0.0;
   out_2729823001511069589[55] = 0.0;
   out_2729823001511069589[56] = 0.0;
   out_2729823001511069589[57] = 0.0;
   out_2729823001511069589[58] = 0.0;
   out_2729823001511069589[59] = 0.0;
   out_2729823001511069589[60] = 1.0;
   out_2729823001511069589[61] = 0.0;
   out_2729823001511069589[62] = 0.0;
   out_2729823001511069589[63] = 0.0;
   out_2729823001511069589[64] = 0.0;
   out_2729823001511069589[65] = 0.0;
   out_2729823001511069589[66] = 0.0;
   out_2729823001511069589[67] = 0.0;
   out_2729823001511069589[68] = 0.0;
   out_2729823001511069589[69] = 0.0;
   out_2729823001511069589[70] = 1.0;
   out_2729823001511069589[71] = 0.0;
   out_2729823001511069589[72] = 0.0;
   out_2729823001511069589[73] = 0.0;
   out_2729823001511069589[74] = 0.0;
   out_2729823001511069589[75] = 0.0;
   out_2729823001511069589[76] = 0.0;
   out_2729823001511069589[77] = 0.0;
   out_2729823001511069589[78] = 0.0;
   out_2729823001511069589[79] = 0.0;
   out_2729823001511069589[80] = 1.0;
}
void f_fun(double *state, double dt, double *out_3238847108558356862) {
   out_3238847108558356862[0] = state[0];
   out_3238847108558356862[1] = state[1];
   out_3238847108558356862[2] = state[2];
   out_3238847108558356862[3] = state[3];
   out_3238847108558356862[4] = state[4];
   out_3238847108558356862[5] = dt*((-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]))*state[6] - 9.8100000000000005*state[8] + stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*state[1]) + (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*state[4])) + state[5];
   out_3238847108558356862[6] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*state[4])) + state[6];
   out_3238847108558356862[7] = state[7];
   out_3238847108558356862[8] = state[8];
}
void F_fun(double *state, double dt, double *out_5580812693562028107) {
   out_5580812693562028107[0] = 1;
   out_5580812693562028107[1] = 0;
   out_5580812693562028107[2] = 0;
   out_5580812693562028107[3] = 0;
   out_5580812693562028107[4] = 0;
   out_5580812693562028107[5] = 0;
   out_5580812693562028107[6] = 0;
   out_5580812693562028107[7] = 0;
   out_5580812693562028107[8] = 0;
   out_5580812693562028107[9] = 0;
   out_5580812693562028107[10] = 1;
   out_5580812693562028107[11] = 0;
   out_5580812693562028107[12] = 0;
   out_5580812693562028107[13] = 0;
   out_5580812693562028107[14] = 0;
   out_5580812693562028107[15] = 0;
   out_5580812693562028107[16] = 0;
   out_5580812693562028107[17] = 0;
   out_5580812693562028107[18] = 0;
   out_5580812693562028107[19] = 0;
   out_5580812693562028107[20] = 1;
   out_5580812693562028107[21] = 0;
   out_5580812693562028107[22] = 0;
   out_5580812693562028107[23] = 0;
   out_5580812693562028107[24] = 0;
   out_5580812693562028107[25] = 0;
   out_5580812693562028107[26] = 0;
   out_5580812693562028107[27] = 0;
   out_5580812693562028107[28] = 0;
   out_5580812693562028107[29] = 0;
   out_5580812693562028107[30] = 1;
   out_5580812693562028107[31] = 0;
   out_5580812693562028107[32] = 0;
   out_5580812693562028107[33] = 0;
   out_5580812693562028107[34] = 0;
   out_5580812693562028107[35] = 0;
   out_5580812693562028107[36] = 0;
   out_5580812693562028107[37] = 0;
   out_5580812693562028107[38] = 0;
   out_5580812693562028107[39] = 0;
   out_5580812693562028107[40] = 1;
   out_5580812693562028107[41] = 0;
   out_5580812693562028107[42] = 0;
   out_5580812693562028107[43] = 0;
   out_5580812693562028107[44] = 0;
   out_5580812693562028107[45] = dt*(stiffness_front*(-state[2] - state[3] + state[7])/(mass*state[1]) + (-stiffness_front - stiffness_rear)*state[5]/(mass*state[4]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[6]/(mass*state[4]));
   out_5580812693562028107[46] = -dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(mass*pow(state[1], 2));
   out_5580812693562028107[47] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5580812693562028107[48] = -dt*stiffness_front*state[0]/(mass*state[1]);
   out_5580812693562028107[49] = dt*((-1 - (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*pow(state[4], 2)))*state[6] - (-stiffness_front*state[0] - stiffness_rear*state[0])*state[5]/(mass*pow(state[4], 2)));
   out_5580812693562028107[50] = dt*(-stiffness_front*state[0] - stiffness_rear*state[0])/(mass*state[4]) + 1;
   out_5580812693562028107[51] = dt*(-state[4] + (-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(mass*state[4]));
   out_5580812693562028107[52] = dt*stiffness_front*state[0]/(mass*state[1]);
   out_5580812693562028107[53] = -9.8100000000000005*dt;
   out_5580812693562028107[54] = dt*(center_to_front*stiffness_front*(-state[2] - state[3] + state[7])/(rotational_inertia*state[1]) + (-center_to_front*stiffness_front + center_to_rear*stiffness_rear)*state[5]/(rotational_inertia*state[4]) + (-pow(center_to_front, 2)*stiffness_front - pow(center_to_rear, 2)*stiffness_rear)*state[6]/(rotational_inertia*state[4]));
   out_5580812693562028107[55] = -center_to_front*dt*stiffness_front*(-state[2] - state[3] + state[7])*state[0]/(rotational_inertia*pow(state[1], 2));
   out_5580812693562028107[56] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5580812693562028107[57] = -center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5580812693562028107[58] = dt*(-(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])*state[5]/(rotational_inertia*pow(state[4], 2)) - (-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])*state[6]/(rotational_inertia*pow(state[4], 2)));
   out_5580812693562028107[59] = dt*(-center_to_front*stiffness_front*state[0] + center_to_rear*stiffness_rear*state[0])/(rotational_inertia*state[4]);
   out_5580812693562028107[60] = dt*(-pow(center_to_front, 2)*stiffness_front*state[0] - pow(center_to_rear, 2)*stiffness_rear*state[0])/(rotational_inertia*state[4]) + 1;
   out_5580812693562028107[61] = center_to_front*dt*stiffness_front*state[0]/(rotational_inertia*state[1]);
   out_5580812693562028107[62] = 0;
   out_5580812693562028107[63] = 0;
   out_5580812693562028107[64] = 0;
   out_5580812693562028107[65] = 0;
   out_5580812693562028107[66] = 0;
   out_5580812693562028107[67] = 0;
   out_5580812693562028107[68] = 0;
   out_5580812693562028107[69] = 0;
   out_5580812693562028107[70] = 1;
   out_5580812693562028107[71] = 0;
   out_5580812693562028107[72] = 0;
   out_5580812693562028107[73] = 0;
   out_5580812693562028107[74] = 0;
   out_5580812693562028107[75] = 0;
   out_5580812693562028107[76] = 0;
   out_5580812693562028107[77] = 0;
   out_5580812693562028107[78] = 0;
   out_5580812693562028107[79] = 0;
   out_5580812693562028107[80] = 1;
}
void h_25(double *state, double *unused, double *out_2449360683753057772) {
   out_2449360683753057772[0] = state[6];
}
void H_25(double *state, double *unused, double *out_7633514826695734429) {
   out_7633514826695734429[0] = 0;
   out_7633514826695734429[1] = 0;
   out_7633514826695734429[2] = 0;
   out_7633514826695734429[3] = 0;
   out_7633514826695734429[4] = 0;
   out_7633514826695734429[5] = 0;
   out_7633514826695734429[6] = 1;
   out_7633514826695734429[7] = 0;
   out_7633514826695734429[8] = 0;
}
void h_24(double *state, double *unused, double *out_2915476860142765873) {
   out_2915476860142765873[0] = state[4];
   out_2915476860142765873[1] = state[5];
}
void H_24(double *state, double *unused, double *out_7236869522341874934) {
   out_7236869522341874934[0] = 0;
   out_7236869522341874934[1] = 0;
   out_7236869522341874934[2] = 0;
   out_7236869522341874934[3] = 0;
   out_7236869522341874934[4] = 1;
   out_7236869522341874934[5] = 0;
   out_7236869522341874934[6] = 0;
   out_7236869522341874934[7] = 0;
   out_7236869522341874934[8] = 0;
   out_7236869522341874934[9] = 0;
   out_7236869522341874934[10] = 0;
   out_7236869522341874934[11] = 0;
   out_7236869522341874934[12] = 0;
   out_7236869522341874934[13] = 0;
   out_7236869522341874934[14] = 1;
   out_7236869522341874934[15] = 0;
   out_7236869522341874934[16] = 0;
   out_7236869522341874934[17] = 0;
}
void h_30(double *state, double *unused, double *out_4267442820011222133) {
   out_4267442820011222133[0] = state[4];
}
void H_30(double *state, double *unused, double *out_3896538905522200432) {
   out_3896538905522200432[0] = 0;
   out_3896538905522200432[1] = 0;
   out_3896538905522200432[2] = 0;
   out_3896538905522200432[3] = 0;
   out_3896538905522200432[4] = 1;
   out_3896538905522200432[5] = 0;
   out_3896538905522200432[6] = 0;
   out_3896538905522200432[7] = 0;
   out_3896538905522200432[8] = 0;
}
void h_26(double *state, double *unused, double *out_1230656768566889448) {
   out_1230656768566889448[0] = state[7];
}
void H_26(double *state, double *unused, double *out_7508703277253016586) {
   out_7508703277253016586[0] = 0;
   out_7508703277253016586[1] = 0;
   out_7508703277253016586[2] = 0;
   out_7508703277253016586[3] = 0;
   out_7508703277253016586[4] = 0;
   out_7508703277253016586[5] = 0;
   out_7508703277253016586[6] = 0;
   out_7508703277253016586[7] = 1;
   out_7508703277253016586[8] = 0;
}
void h_27(double *state, double *unused, double *out_5053766004561755423) {
   out_5053766004561755423[0] = state[3];
}
void H_27(double *state, double *unused, double *out_6071302217322625343) {
   out_6071302217322625343[0] = 0;
   out_6071302217322625343[1] = 0;
   out_6071302217322625343[2] = 0;
   out_6071302217322625343[3] = 1;
   out_6071302217322625343[4] = 0;
   out_6071302217322625343[5] = 0;
   out_6071302217322625343[6] = 0;
   out_6071302217322625343[7] = 0;
   out_6071302217322625343[8] = 0;
}
void h_29(double *state, double *unused, double *out_5210952672912884568) {
   out_5210952672912884568[0] = state[1];
}
void H_29(double *state, double *unused, double *out_7784664944192176376) {
   out_7784664944192176376[0] = 0;
   out_7784664944192176376[1] = 1;
   out_7784664944192176376[2] = 0;
   out_7784664944192176376[3] = 0;
   out_7784664944192176376[4] = 0;
   out_7784664944192176376[5] = 0;
   out_7784664944192176376[6] = 0;
   out_7784664944192176376[7] = 0;
   out_7784664944192176376[8] = 0;
}
void h_28(double *state, double *unused, double *out_5957834634719095380) {
   out_5957834634719095380[0] = state[0];
}
void H_28(double *state, double *unused, double *out_5579680112447844666) {
   out_5579680112447844666[0] = 1;
   out_5579680112447844666[1] = 0;
   out_5579680112447844666[2] = 0;
   out_5579680112447844666[3] = 0;
   out_5579680112447844666[4] = 0;
   out_5579680112447844666[5] = 0;
   out_5579680112447844666[6] = 0;
   out_5579680112447844666[7] = 0;
   out_5579680112447844666[8] = 0;
}
void h_31(double *state, double *unused, double *out_8116110739202444659) {
   out_8116110739202444659[0] = state[8];
}
void H_31(double *state, double *unused, double *out_7664160788572694857) {
   out_7664160788572694857[0] = 0;
   out_7664160788572694857[1] = 0;
   out_7664160788572694857[2] = 0;
   out_7664160788572694857[3] = 0;
   out_7664160788572694857[4] = 0;
   out_7664160788572694857[5] = 0;
   out_7664160788572694857[6] = 0;
   out_7664160788572694857[7] = 0;
   out_7664160788572694857[8] = 1;
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
void car_err_fun(double *nom_x, double *delta_x, double *out_1176760182641486560) {
  err_fun(nom_x, delta_x, out_1176760182641486560);
}
void car_inv_err_fun(double *nom_x, double *true_x, double *out_2893373232090748310) {
  inv_err_fun(nom_x, true_x, out_2893373232090748310);
}
void car_H_mod_fun(double *state, double *out_2729823001511069589) {
  H_mod_fun(state, out_2729823001511069589);
}
void car_f_fun(double *state, double dt, double *out_3238847108558356862) {
  f_fun(state,  dt, out_3238847108558356862);
}
void car_F_fun(double *state, double dt, double *out_5580812693562028107) {
  F_fun(state,  dt, out_5580812693562028107);
}
void car_h_25(double *state, double *unused, double *out_2449360683753057772) {
  h_25(state, unused, out_2449360683753057772);
}
void car_H_25(double *state, double *unused, double *out_7633514826695734429) {
  H_25(state, unused, out_7633514826695734429);
}
void car_h_24(double *state, double *unused, double *out_2915476860142765873) {
  h_24(state, unused, out_2915476860142765873);
}
void car_H_24(double *state, double *unused, double *out_7236869522341874934) {
  H_24(state, unused, out_7236869522341874934);
}
void car_h_30(double *state, double *unused, double *out_4267442820011222133) {
  h_30(state, unused, out_4267442820011222133);
}
void car_H_30(double *state, double *unused, double *out_3896538905522200432) {
  H_30(state, unused, out_3896538905522200432);
}
void car_h_26(double *state, double *unused, double *out_1230656768566889448) {
  h_26(state, unused, out_1230656768566889448);
}
void car_H_26(double *state, double *unused, double *out_7508703277253016586) {
  H_26(state, unused, out_7508703277253016586);
}
void car_h_27(double *state, double *unused, double *out_5053766004561755423) {
  h_27(state, unused, out_5053766004561755423);
}
void car_H_27(double *state, double *unused, double *out_6071302217322625343) {
  H_27(state, unused, out_6071302217322625343);
}
void car_h_29(double *state, double *unused, double *out_5210952672912884568) {
  h_29(state, unused, out_5210952672912884568);
}
void car_H_29(double *state, double *unused, double *out_7784664944192176376) {
  H_29(state, unused, out_7784664944192176376);
}
void car_h_28(double *state, double *unused, double *out_5957834634719095380) {
  h_28(state, unused, out_5957834634719095380);
}
void car_H_28(double *state, double *unused, double *out_5579680112447844666) {
  H_28(state, unused, out_5579680112447844666);
}
void car_h_31(double *state, double *unused, double *out_8116110739202444659) {
  h_31(state, unused, out_8116110739202444659);
}
void car_H_31(double *state, double *unused, double *out_7664160788572694857) {
  H_31(state, unused, out_7664160788572694857);
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
