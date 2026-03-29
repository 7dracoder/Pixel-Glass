import Foundation
import CoreLocation

class LocationManager: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published var lastLocation: CLLocation?
    @Published var authorizationStatus: CLAuthorizationStatus

    private let manager = CLLocationManager()

    override init() {
        self.authorizationStatus = manager.authorizationStatus
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyBest
    }

    func requestPermission() {
        NSLog("[LocationManager] Requesting permission, current status: %d", authorizationStatus.rawValue)
        manager.requestWhenInUseAuthorization()
    }

    func getCurrentLocation() -> CLLocation? {
        let status = authorizationStatus
        NSLog("[LocationManager] getCurrentLocation called, status: %d", status.rawValue)
        
        // Hardcoded fallback location (New York City)
        let fallbackLocation = CLLocation(latitude: 40.7126, longitude: -74.0066)
        
        guard status == .authorizedWhenInUse || status == .authorizedAlways else {
            NSLog("[LocationManager] Not authorized, using fallback location")
            return fallbackLocation
        }
        
        // Try to get cached location first
        if let cached = manager.location {
            NSLog("[LocationManager] Using cached location: %.4f, %.4f", 
                  cached.coordinate.latitude, cached.coordinate.longitude)
            lastLocation = cached
            return cached
        }
        
        // Request a fresh location (async, will update lastLocation via delegate)
        manager.requestLocation()
        
        // Return lastLocation if we have one from a previous request
        if let last = lastLocation {
            NSLog("[LocationManager] Using lastLocation: %.4f, %.4f",
                  last.coordinate.latitude, last.coordinate.longitude)
            return last
        }
        
        NSLog("[LocationManager] No GPS fix yet, using fallback location")
        return fallbackLocation
    }

    // MARK: - CLLocationManagerDelegate

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        authorizationStatus = manager.authorizationStatus
        NSLog("[LocationManager] Authorization changed to: %d", authorizationStatus.rawValue)
        
        // Start location updates when authorized
        if authorizationStatus == .authorizedWhenInUse || authorizationStatus == .authorizedAlways {
            manager.requestLocation()
        }
    }

    func locationManager(_ mgr: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        if let location = locations.last {
            lastLocation = location
            NSLog("[LocationManager] Got location: %.4f, %.4f", 
                  location.coordinate.latitude, location.coordinate.longitude)
        }
    }

    func locationManager(_ mgr: CLLocationManager, didFailWithError error: Error) {
        NSLog("[LocationManager] Location error: %@", error.localizedDescription)
    }
}
