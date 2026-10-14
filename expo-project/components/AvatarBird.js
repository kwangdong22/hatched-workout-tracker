import React, { useRef, useState } from 'react';
import {
  Animated,
  TouchableOpacity,
  View,
  Image,
  Text,
  StyleSheet,
  Easing,
} from 'react-native';

const AVATAR_IMAGES = {
  egg:   require('../assets/avatars/avatar-egg.png'),
  chick: require('../assets/avatars/avatar-chick.png'),
  bird:  require('../assets/avatars/avatar-bird.png'),
};

const STAGE_LABELS = {
  egg:   'Keep going...',
  chick: 'Getting stronger!',
  bird:  'Tap me!',
};

function getStage(streakDays) {
  if (streakDays < 30) return 'egg';
  if (streakDays < 60) return 'chick';
  return 'bird';
}

export default function AvatarBird({ streakDays = 0, currentStage = null }) {
  const stage = currentStage === 'baby_bird' ? 'chick'
    : currentStage === 'flying_bird' ? 'bird'
    : currentStage === 'egg' ? 'egg'
    : getStage(streakDays);

  const [isAnimating, setIsAnimating] = useState(false);

  // Animation refs
  const orbitAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePress = () => {
    if (stage !== 'bird' || isAnimating) return;
    setIsAnimating(true);

    const DURATION = 2000;

    // Reset
    orbitAnim.setValue(0);
    scaleAnim.setValue(1);

    Animated.parallel([
      Animated.timing(orbitAnim, {
        toValue: 1,
        duration: DURATION,
        easing: Easing.linear,
        useNativeDriver: true,
      }),
      Animated.sequence([
        Animated.timing(scaleAnim, {
          toValue: 1.25,
          duration: DURATION / 2,
          easing: Easing.out(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: DURATION / 2,
          easing: Easing.in(Easing.ease),
          useNativeDriver: true,
        }),
      ]),
    ]).start(() => {
      orbitAnim.setValue(0);
      scaleAnim.setValue(1);
      setIsAnimating(false);
    });
  };

  const RADIUS = 100;

  // At rest (orbitAnim = 0 or 1), displacement is (0, 0)
  const translateX = orbitAnim.interpolate({
    inputRange:  [0, 0.25, 0.5, 0.75, 1],
    outputRange: [0, RADIUS, 0, -RADIUS, 0],
  });

  const translateY = orbitAnim.interpolate({
    inputRange:  [0, 0.25, 0.5, 0.75, 1],
    outputRange: [0, -RADIUS, 0, RADIUS, 0],
  });

  return (
    <View style={styles.wrapper}>
      <TouchableOpacity
        onPress={handlePress}
        activeOpacity={stage === 'bird' ? 0.85 : 1}
        disabled={stage !== 'bird' || isAnimating}
      >
        <Animated.View
          style={[
            styles.avatarContainer,
            {
              transform: [
                { translateX },
                { translateY },
                { scale: scaleAnim },
              ],
            },
          ]}
        >
          <Image
            source={AVATAR_IMAGES[stage]}
            style={styles.avatar}
            resizeMode="contain"
          />
        </Animated.View>
      </TouchableOpacity>

      <Text style={styles.hint}>{STAGE_LABELS[stage]}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    alignItems: 'center',
    justifyContent: 'center',
    height: 320,
  },
  avatarContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FAF6F0',
  },
  avatar: {
    width: 200,
    height: 200,
  },
  hint: {
    marginTop: 12,
    fontSize: 13,
    color: '#B0A080',
    fontStyle: 'italic',
    letterSpacing: 0.3,
  },
});
