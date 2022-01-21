import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
import numpy as np
import pdb


class smoothing():

    def __init__(self, skipEveryNpoints):

        self.skipEveryNpoints = skipEveryNpoints

    def setPoints(self, xdata, ydata, zdata, rolldata, yawdata, pitchdata, dtime, speed):

        # Computed the spline for the asked distances:
        subdivision = len(xdata) * 3
        self.alpha = np.linspace(0, 1, subdivision)

        coord = np.array([xdata, ydata, zdata]).T
        orientation = np.array([rolldata, yawdata, pitchdata]).T
        dtime = np.array([dtime], dtype=np.float64)
        speed = np.array([speed])

        tmpTime = self.smoothData(dtime)[0]
        self.data = {
            "position": self.smoothData(coord),
            "orientation": self.smoothData(orientation),
            "time": [np.where(tmpTime < 0, 0, tmpTime)][0], # to have only positive values
            "speed": self.smoothData(speed)[0]
        }

        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        # ax.set_xlabel('X Label')
        # ax.set_ylabel('Y Label')
        # ax.set_zlabel('Z Label')

        # ax.scatter(self.coordData[0], self.coordData[1], self.coordData[2], s=self.speedData[0],c=self.speedData[0])
        # #ax.scatter(points[:,0], points[:,1], points[:,2], c='grey')
        # plt.draw()
        # plt.show()
        # pdb.set_trace()


    def smoothCalculation(self):

        return self.data["position"][0], self.data["position"][1], self.data["position"][2], self.data["orientation"][0], self.data["orientation"][1], self.data["orientation"][2], self.data["time"], self.data["speed"]


    def skipEveryNpointsFunc(self):

        # skip each n points, to have a better view of data
        self.data["position"][0] = self.data["position"][0][::self.skipEveryNpoints]
        self.data["position"][1] = self.data["position"][1][::self.skipEveryNpoints]
        self.data["position"][2] = self.data["position"][2][::self.skipEveryNpoints]

        self.data["orientation"][0] = self.data["orientation"][0][::self.skipEveryNpoints]
        self.data["orientation"][1] = self.data["orientation"][1][::self.skipEveryNpoints]
        self.data["orientation"][2] = self.data["orientation"][2][::self.skipEveryNpoints]

        self.data["time"] = self.data["time"][::self.skipEveryNpoints]

        self.data["speed"] = self.data["speed"][::self.skipEveryNpoints]


    def smoothData(self, data):

        # Linear length along the line:
        if data.shape[0] == 1:
            distance = np.cumsum( np.sqrt(np.sum( np.diff(data, axis=1)**2, axis=0 )) )

            distance = np.insert(distance, 0, 0)/distance[-1]

            spline = UnivariateSpline(distance, data, k=3)

            return [spline(self.alpha)]
        else:
            distance = np.cumsum( np.sqrt(np.sum( np.diff(data, axis=0)**2, axis=1 )) )

            distance = np.insert(distance, 0, 0)/distance[-1]
            
            # Build a list of the spline function, one for each dimension:
            splines = [UnivariateSpline(distance, coords, k=3, s=.2) for coords in data.T]

        out = []
        for spline in splines:
            out.append(spline(self.alpha))

        return out


def main():

    # Define some points:
    theta = np.linspace(-3, 2, 40)
    points = np.vstack( (np.vstack( (np.cos(theta), np.sin(theta)) ), np.tanh(theta)) ).T

    # add some noise:
    points = points + 0.05*np.random.randn(*points.shape)

    # Linear length along the line:
    distance = np.cumsum( np.sqrt(np.sum( np.diff(points, axis=0)**2, axis=1 )) )
    distance = np.insert(distance, 0, 0)/distance[-1]

    # Build a list of the spline function, one for each dimension:
    splines = [UnivariateSpline(distance, coords, k=3, s=.2) for coords in points.T]

    # Computed the spline for the asked distances:
    alpha = np.linspace(0, 1, 75)
    #points_fitted = np.vstack( (splines[0](alpha), splines[1](alpha), splines[2](alpha)) ).T

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    ax.scatter(splines[0](alpha), splines[1](alpha), splines[2](alpha), c=splines[2](alpha))
    ax.scatter(points[:,0], points[:,1], points[:,2], c='grey')
    plt.draw()
    plt.show()


if __name__ == "__main__":

    main()